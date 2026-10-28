import hashlib
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
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
from backend.app.agents.agent_2.app.schemas import RoutingProposal
from backend.app.agents.monitoring_escalation import EscalationOutcome, EscalationProposal
from backend.app.config import Settings
from backend.app.database import Base, get_session
from backend.app.main import app
from backend.app.models import (
    AgentRun,
    BackgroundJob,
    Complaint,
    ComplaintAnalysis,
    ComplaintEvent,
    ComplaintMedia,
    MonitoringAuthority,
    MonitoringCase,
    MonitoringEvent,
    MonitoringJob,
)
from backend.app.security import Actor, get_current_analyst_reviewer
from backend.app.services import get_complaint_analysis, submit_complaint_with_image
from backend.app.storage import PrivateLocalMediaStore
from backend.app.workers.complaint_analysis_worker import ComplaintAnalysisWorker, utc_now
from backend.app.workers.monitoring_worker import MonitoringWorker
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


class StubResolutionWorkflow:
    def run(self, complaint):
        return RoutingProposal(
            complaint_id=complaint.complaint_id,
            parent_task_title="Test routing proposal",
        )


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

    def worker(self, fake_analyst, accepted_assignment_provider=None):
        return ComplaintAnalysisWorker(
            session_factory=self.sessions,
            media_store=self.storage,
            analyst_factory=lambda: fake_analyst,
            settings=self.settings,
            resolution_workflow_factory=StubResolutionWorkflow,
            accepted_assignment_provider=accepted_assignment_provider,
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
        with self.sessions() as session:
            session.get(Complaint, self.complaint.id).description = "Test road complaint."
            session.commit()
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
            self.assertEqual(saved.routing_proposal["parent_task_title"], "Test routing proposal")
            self.assertEqual(saved.agent_run_id, run.id)
            self.assertEqual(complaint.status, "submitted")
            self.assertIsNone(
                session.scalar(select(MonitoringCase).where(MonitoringCase.complaint_id == complaint.id))
            )

    def test_agent2_failure_does_not_change_saved_agent1_success(self):
        class FailedResolutionWorkflow:
            def run(self, complaint):
                raise RuntimeError("routing provider unavailable")

        with self.sessions() as session:
            session.get(Complaint, self.complaint.id).description = "Test road complaint."
            session.commit()
        worker = ComplaintAnalysisWorker(
            session_factory=self.sessions,
            media_store=self.storage,
            analyst_factory=lambda: StubAnalyst(),
            settings=self.settings,
            resolution_workflow_factory=FailedResolutionWorkflow,
            worker_id="agent2-failure-test",
        )

        self.assertTrue(worker.process_one())
        with self.sessions() as session:
            job = session.get(BackgroundJob, self.job.id)
            saved = session.scalar(
                select(ComplaintAnalysis).where(ComplaintAnalysis.complaint_id == self.complaint.id)
            )
            self.assertEqual(job.status, "succeeded")
            self.assertEqual(saved.result["category"], IssueCategory.ROADS_POTHOLES.value)
            self.assertIsNone(saved.routing_proposal)

    def test_development_fixture_connects_agent2_to_agent3_worker(self):
        """Synthetic-only assignment/SLA fixture; never municipal reference data."""
        complaint_reference = "DEV-A3-TEST-0001"
        dev_owner = "development-only:agent3-fixture"
        test_authority = MonitoringAuthority(
            subject="development-only:senior-authority",
            display_name="Development-only senior authority",
            authority_type="senior_authority",
            jurisdiction_id="DEVELOPMENT_ONLY_JURISDICTION",
            department_id="DEVELOPMENT_ONLY_DEPARTMENT",
            escalation_level=1,
            eligibility_basis="Development test fixture only; not a real authority.",
            active=True,
        )
        with self.sessions() as session:
            complaint = session.get(Complaint, self.complaint.id)
            complaint.public_reference = complaint_reference
            complaint.owner_subject = dev_owner
            complaint.description = "Development-only road issue fixture."
            session.add(test_authority)
            session.commit()
            authority_id = test_authority.id

        def development_assignment_provider(session, complaint_id, reference, owner, routing_proposal):
            if (
                reference != complaint_reference
                or owner != dev_owner
                or routing_proposal.get("complaint_id") != str(complaint_id)
            ):
                return None
            return {
                "jurisdiction_id": "DEVELOPMENT_ONLY_JURISDICTION",
                "department_id": "DEVELOPMENT_ONLY_DEPARTMENT",
                "assigned_officer_subject": "development-only:assigned-officer",
                "sla_policy_id": "DEVELOPMENT_ONLY_TEST_POLICY",
                "sla_policy_version": "fixture-1",
                "sla_deadline_at": datetime(2020, 1, 1, tzinfo=timezone.utc),
            }

        self.assertTrue(
            self.worker(
                StubAnalyst(),
                accepted_assignment_provider=development_assignment_provider,
            ).process_one()
        )

        with self.sessions() as session:
            case = session.scalar(
                select(MonitoringCase).where(MonitoringCase.complaint_id == self.complaint.id)
            )
            saved_analysis = session.scalar(
                select(ComplaintAnalysis).where(ComplaintAnalysis.complaint_id == self.complaint.id)
            )
            self.assertIsNotNone(case)
            self.assertEqual(case.sla_deadline_at.replace(tzinfo=timezone.utc), datetime(2020, 1, 1, tzinfo=timezone.utc))
            self.assertEqual(case.sla_policy_id, "DEVELOPMENT_ONLY_TEST_POLICY")
            self.assertIsNotNone(saved_analysis.routing_proposal)
            self.assertEqual(saved_analysis.result["category"], IssueCategory.ROADS_POTHOLES.value)

        class StubEscalationAgent:
            def handle(self, event):
                self.event = event
                return EscalationProposal(
                    outcome=EscalationOutcome.COMPLETED,
                    breach_summary="Development-only confirmed breach fixture.",
                    recommended_authority_id=str(authority_id),
                )

        monitoring_worker = MonitoringWorker(
            session_factory=self.sessions,
            agent_factory=StubEscalationAgent,
            settings=self.settings,
            worker_id="development-only-monitoring-worker",
        )
        # SQLite drops timezone metadata when reading DateTime columns, so this
        # test clock is naive; register_monitoring_case received an aware deadline.
        self.assertEqual(monitoring_worker.scan_due_sla_cases(now=datetime(2021, 1, 1)), 1)
        self.assertTrue(monitoring_worker.process_one_agent_job())
        with self.sessions() as session:
            case = session.scalar(
                select(MonitoringCase).where(MonitoringCase.complaint_id == self.complaint.id)
            )
            job = session.scalar(select(MonitoringJob).where(MonitoringJob.monitoring_case_id == case.id))
            breach = session.scalar(
                select(MonitoringEvent).where(
                    MonitoringEvent.monitoring_case_id == case.id,
                    MonitoringEvent.event_type == "SLA_BREACHED",
                )
            )
            self.assertEqual(case.sla_status, "breached")
            self.assertEqual(job.status, "succeeded")
            self.assertEqual(job.result["breach_summary"], "Development-only confirmed breach fixture.")
            self.assertIsNotNone(breach)
            job_id = job.id

        def override_session():
            with self.sessions() as session:
                yield session

        app.dependency_overrides[get_session] = override_session
        app.dependency_overrides[get_current_analyst_reviewer] = lambda: Actor(
            subject="development-only:staff-reviewer", role="staff"
        )
        try:
            from fastapi.testclient import TestClient

            with TestClient(app) as client:
                response = client.get(f"/api/v1/staff/monitoring/escalation-jobs/{job_id}")
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(
                response.json()["proposal"]["breach_summary"],
                "Development-only confirmed breach fixture.",
            )
        finally:
            app.dependency_overrides.pop(get_session, None)
            app.dependency_overrides.pop(get_current_analyst_reviewer, None)

    def test_job_lease_prevents_second_worker_claim_and_recovers_expired_attempt(self):
        first_worker = self.worker(StubAnalyst())
        second_worker = ComplaintAnalysisWorker(
            session_factory=self.sessions,
            media_store=self.storage,
            analyst_factory=lambda: StubAnalyst(),
            settings=self.settings,
            resolution_workflow_factory=StubResolutionWorkflow,
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
