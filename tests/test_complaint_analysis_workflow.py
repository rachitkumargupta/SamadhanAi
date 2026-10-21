import hashlib
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.agents.complaint_analyst import (
    ANALYSIS_SCHEMA_VERSION,
    AnalystProviderError,
    AnalystUnavailable,
    AnalysisOutcome,
    ComplaintAnalysis as Proposal,
    IssueCategory,
    RecommendationLevel,
    normalize_image,
)
from backend.app.config import Settings
from backend.app.database import Base
from backend.app.models import (
    AgentRun,
    BackgroundJob,
    Complaint,
    ComplaintAnalysis,
    ComplaintEvent,
    ComplaintMedia,
)
from backend.app.services import get_complaint_analysis, submit_complaint_with_image
from backend.app.storage import PrivateLocalMediaStore
from backend.app.workers.complaint_analysis_worker import ComplaintAnalysisWorker, utc_now
from test_complaint_analyst import image_bytes


def proposal():
    return Proposal(
        schema_version=ANALYSIS_SCHEMA_VERSION,
        outcome=AnalysisOutcome.COMPLETED,
        generated_description="A road surface appears damaged.",
        visible_evidence=["A depression is visible in the road."],
        facts=["The road surface is uneven."],
        inferences=["The issue may be a pothole."],
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


class StubAnalyst:
    def __init__(self, result=None, error=None):
        self.result = result or proposal()
        self.error = error

    def analyze(self, request):
        if self.error:
            raise self.error
        return self.result


class ComplaintAnalysisWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage = PrivateLocalMediaStore(Path(self.temp_dir.name) / "private")
        self.settings = Settings(
            database_url="sqlite+pysqlite:///:memory:",
            jwt_secret="x" * 32,
            jwt_issuer="https://issuer.invalid",
            jwt_audience="samadhan-test",
            complaint_media_storage_dir=str(Path(self.temp_dir.name) / "private"),
        )
        self.normalized_image, _ = normalize_image(image_bytes())
        self.object_key = self.storage.save_image(self.normalized_image)
        with self.sessions() as session:
            self.complaint, self.job = submit_complaint_with_image(
                session,
                actor_subject="citizen-1",
                description=None,
                location_text="Ward 4",
                correlation_id="12345678-1234-5678-1234-567812345678",
                object_key=self.object_key,
                normalized_image=self.normalized_image,
            )

    def tearDown(self):
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()
        self.temp_dir.cleanup()

    def worker(self, fake_analyst):
        return ComplaintAnalysisWorker(
            session_factory=self.sessions,
            media_store=self.storage,
            analyst_factory=lambda: fake_analyst,
            settings=self.settings,
            worker_id="test-worker",
        )

    def test_intake_atomically_persists_complaint_media_event_and_job(self):
        with self.sessions() as session:
            complaint = session.get(Complaint, self.complaint.id)
            media = session.scalar(select(ComplaintMedia).where(ComplaintMedia.complaint_id == complaint.id))
            event = session.scalar(select(ComplaintEvent).where(ComplaintEvent.complaint_id == complaint.id))
            job = session.get(BackgroundJob, self.job.id)
            self.assertIsNone(complaint.description)
            self.assertIsNotNone(media)
            self.assertEqual(media.sha256, hashlib.sha256(self.normalized_image).hexdigest())
            self.assertEqual(event.correlation_id, "12345678-1234-5678-1234-567812345678")
            self.assertEqual(job.status, "pending")
            self.assertEqual(job.idempotency_key, f"complaint_analysis:{complaint.id}")
            job_status, analysis = get_complaint_analysis(session, complaint_id=complaint.id)
            self.assertEqual(job_status.status, "pending")
            self.assertIsNone(analysis)

    def test_worker_persists_result_and_run_without_changing_complaint_state(self):
        self.assertTrue(self.worker(StubAnalyst()).process_one())
        with self.sessions() as session:
            job = session.get(BackgroundJob, self.job.id)
            complaint = session.get(Complaint, self.complaint.id)
            run = session.scalar(select(AgentRun).where(AgentRun.job_id == self.job.id))
            saved = session.scalar(
                select(ComplaintAnalysis).where(ComplaintAnalysis.complaint_id == self.complaint.id)
            )
            self.assertEqual(job.status, "succeeded")
            self.assertEqual(run.status, "completed")
            self.assertEqual(saved.result["category"], IssueCategory.ROADS_POTHOLES.value)
            self.assertEqual(saved.agent_run_id, run.id)
            self.assertEqual(complaint.status, "submitted")

    def test_job_lease_prevents_second_worker_claim_and_recovers_expired_attempt(self):
        first_worker = self.worker(StubAnalyst())
        second_worker = ComplaintAnalysisWorker(
            session_factory=self.sessions,
            media_store=self.storage,
            analyst_factory=lambda: StubAnalyst(),
            settings=self.settings,
            worker_id="second-worker",
        )
        self.assertEqual(first_worker.claim_one(), self.job.id)
        self.assertIsNone(second_worker.claim_one())
        with self.sessions() as session:
            job = session.get(BackgroundJob, self.job.id)
            job.attempt_count = job.max_attempts
            job.lease_expires_at = utc_now() - timedelta(seconds=1)
            session.add(
                AgentRun(
                    complaint_id=self.complaint.id,
                    job_id=job.id,
                    attempt_number=job.attempt_count,
                    agent_name="complaint_analyst",
                    provider="openai",
                    model=self.settings.complaint_analyst_model,
                    schema_version=ANALYSIS_SCHEMA_VERSION,
                    status="running",
                )
            )
            session.commit()
        self.assertIsNone(second_worker.claim_one())
        with self.sessions() as session:
            job = session.get(BackgroundJob, self.job.id)
            run = session.scalar(select(AgentRun).where(AgentRun.job_id == job.id))
            self.assertEqual(job.status, "failed")
            self.assertEqual(job.error_code, "worker_attempts_exhausted")
            self.assertEqual(run.status, "abandoned")

    def test_provider_failures_are_retried_and_terminal_failure_is_reviewable(self):
        worker = self.worker(StubAnalyst(error=AnalystProviderError("private details")))
        for attempt in range(1, 4):
            if attempt > 1:
                with self.sessions() as session:
                    job = session.get(BackgroundJob, self.job.id)
                    job.available_at = utc_now() - timedelta(seconds=1)
                    session.commit()
            worker.process_one()
        with self.sessions() as session:
            job = session.get(BackgroundJob, self.job.id)
            runs = list(session.scalars(select(AgentRun).where(AgentRun.job_id == job.id)).all())
            self.assertEqual(job.status, "failed")
            self.assertEqual(job.error_code, "provider_analysis_failed")
            self.assertEqual(job.attempt_count, 3)
            self.assertEqual(len(runs), 3)
            self.assertTrue(all(run.status == "failed" for run in runs))
            self.assertFalse(any("private details" in (run.error_code or "") for run in runs))

    def test_missing_provider_configuration_fails_without_fabricating_analysis(self):
        worker = self.worker(StubAnalyst(error=RuntimeError("unused")))
        worker._analyst_factory = lambda: (_ for _ in ()).throw(AnalystUnavailable())
        worker.process_one()
        with self.sessions() as session:
            job = session.get(BackgroundJob, self.job.id)
            self.assertEqual(job.status, "failed")
            self.assertEqual(job.error_code, "provider_not_configured")
            self.assertIsNone(session.scalar(select(ComplaintAnalysis)))


if __name__ == "__main__":
    unittest.main()
