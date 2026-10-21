import os
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-signing-secret-that-is-at-least-32-bytes")
os.environ.setdefault("JWT_ISSUER", "https://issuer.invalid")
os.environ.setdefault("JWT_AUDIENCE", "samadhan-test")

from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.agents.complaint_analyst import (
    ANALYSIS_SCHEMA_VERSION,
    AnalysisOutcome,
    ComplaintAnalysis as Proposal,
    IssueCategory,
    RecommendationLevel,
)
from backend.app.config import Settings
from backend.app.database import Base, get_session
from backend.app.main import app
from backend.app.models import BackgroundJob
from backend.app.security import Actor, get_current_citizen
from backend.app.storage import PrivateLocalMediaStore
from backend.app.workers.complaint_analysis_worker import ComplaintAnalysisWorker
from test_complaint_analysis_workflow import StubAnalyst


class ComplaintAnalysisApiTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.temp_dir = tempfile.TemporaryDirectory()
        self.settings = Settings(
            database_url="sqlite+pysqlite:///:memory:",
            jwt_secret="test-signing-secret-that-is-at-least-32-bytes",
            jwt_issuer="https://issuer.invalid",
            jwt_audience="samadhan-test",
            complaint_media_storage_dir=str(Path(self.temp_dir.name) / "private"),
        )

        def override_session():
            with self.sessions() as session:
                yield session

        app.dependency_overrides[get_session] = override_session
        app.dependency_overrides[get_current_citizen] = lambda: Actor(
            subject="citizen-api-test", role="citizen"
        )
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        self.client.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()
        self.temp_dir.cleanup()

    @staticmethod
    def image_upload():
        output = BytesIO()
        Image.new("RGB", (12, 12), color="gray").save(output, format="PNG")
        return output.getvalue()

    def test_multipart_intake_queues_job_and_status_endpoint_returns_saved_result(self):
        with patch("backend.app.routes.get_settings", return_value=self.settings):
            response = self.client.post(
                "/api/v1/complaints",
                files={"image": ("issue.png", self.image_upload(), "image/png")},
                data={"location_text": "Ward 4"},
            )
        self.assertEqual(response.status_code, 201, response.text)
        submitted = response.json()
        self.assertIsNone(submitted["description"])
        self.assertEqual(submitted["analysis_status"], "pending")

        with self.sessions() as session:
            job = session.scalar(select(BackgroundJob))
            self.assertIsNotNone(job)
            job_id = job.id
            complaint_id = job.complaint_id

        result = Proposal(
            schema_version=ANALYSIS_SCHEMA_VERSION,
            outcome=AnalysisOutcome.COMPLETED,
            generated_description="A civic issue is visible.",
            visible_evidence=["A damaged surface is visible."],
            facts=["A surface is damaged."],
            inferences=["It may be a pothole."],
            category=IssueCategory.ROADS_POTHOLES.value,
            severity_recommendation=RecommendationLevel.MEDIUM,
            priority_recommendation=RecommendationLevel.MEDIUM,
            uncertainty=[],
            missing_information=[],
            contradictory_information=[],
            possible_multi_department=False,
            human_review_recommended=False,
            human_review_reasons=[],
        )
        worker = ComplaintAnalysisWorker(
            session_factory=self.sessions,
            media_store=PrivateLocalMediaStore(self.settings.complaint_media_storage_dir),
            analyst_factory=lambda: StubAnalyst(result=result),
            settings=self.settings,
            worker_id="api-test-worker",
        )
        self.assertTrue(worker.process_one())
        with self.sessions() as session:
            persisted_job = session.get(BackgroundJob, job_id)
            self.assertEqual(persisted_job.complaint_id, complaint_id)
            self.assertEqual(persisted_job.status, "succeeded")

        analysis_response = self.client.get(
            f"/api/v1/complaints/{submitted['public_reference']}/analysis"
        )
        self.assertEqual(analysis_response.status_code, 200, analysis_response.text)
        body = analysis_response.json()
        self.assertEqual(body["status"], "succeeded")
        self.assertIsNotNone(body["run_id"])
        self.assertEqual(body["result"]["category"], IssueCategory.ROADS_POTHOLES.value)
        app.dependency_overrides[get_current_citizen] = lambda: Actor(
            subject="another-citizen", role="citizen"
        )
        hidden_response = self.client.get(
            f"/api/v1/complaints/{submitted['public_reference']}/analysis"
        )
        self.assertEqual(hidden_response.status_code, 404)

    def test_analysis_endpoint_requires_authentication(self):
        app.dependency_overrides.pop(get_current_citizen)
        response = self.client.get("/api/v1/complaints/SAM-UNKNOWN/analysis")
        self.assertEqual(response.status_code, 401)

    def test_invalid_image_is_rejected_and_not_persisted(self):
        with patch("backend.app.routes.get_settings", return_value=self.settings):
            response = self.client.post(
                "/api/v1/complaints",
                files={"image": ("issue.png", b"not an image", "image/png")},
            )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["error"]["code"], "invalid_image")
        with self.sessions() as session:
            self.assertEqual(session.scalar(select(func.count()).select_from(BackgroundJob)), 0)
        stored_files = list((Path(self.temp_dir.name) / "private").glob("*"))
        self.assertEqual(stored_files, [])


if __name__ == "__main__":
    unittest.main()
