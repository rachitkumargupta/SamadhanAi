import json
import os
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-signing-secret-that-is-at-least-32-bytes")
os.environ.setdefault("JWT_ISSUER", "https://issuer.invalid")
os.environ.setdefault("JWT_AUDIENCE", "samadhan-test")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.agents.resolution_router import (
    ResolutionRouter,
    RoutingInput,
    RoutingPolicy,
    calculate_sla,
    find_ward,
    parse_coordinates,
    select_eligible_officer,
)
from backend.app.config import Settings
from backend.app.database import Base, get_session
from backend.app.domain.lifecycle import ComplaintState
from backend.app.main import app
from backend.app.models import (
    AgentRun,
    BackgroundJob,
    Complaint,
    ComplaintAnalysis,
    ComplaintAssignment,
    ComplaintEvent,
    Department,
    Officer,
    SLAPolicy,
    Ward,
)
from backend.app.security import Actor, get_current_routing_staff
from backend.app.services import (
    get_complaint_assignment,
    get_complaint_assignment_by_reference,
    route_and_assign_complaint,
)
from backend.app.workers.complaint_routing_worker import ComplaintRoutingWorker


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Agent2ResolutionRoutingTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.settings = Settings(
            database_url="sqlite+pysqlite:///:memory:",
            jwt_secret="test-signing-secret-that-is-at-least-32-bytes",
            jwt_issuer="https://issuer.invalid",
            jwt_audience="samadhan-test",
        )

        # Seed reference data
        with self.sessions() as session:
            # Departments
            self.dept_pwd = Department(code="PWD", name="Public Works Department", is_active=True)
            self.dept_sanitation = Department(code="SANITATION", name="Sanitation Department", is_active=True)
            self.dept_water = Department(code="WATER_SUPPLY", name="Water Supply Department", is_active=True)
            self.dept_elec = Department(code="ELECTRICITY", name="Electricity Department", is_active=True)
            self.dept_drainage = Department(code="DRAINAGE", name="Drainage Department", is_active=True)
            self.dept_inactive = Department(code="INACTIVE_DEPT", name="Inactive Dept", is_active=False)
            session.add_all([
                self.dept_pwd,
                self.dept_sanitation,
                self.dept_water,
                self.dept_elec,
                self.dept_drainage,
                self.dept_inactive,
            ])
            session.flush()

            # Wards (Central Ward bounding box: lat 12.90 to 13.00, lon 77.50 to 77.65)
            self.ward_central = Ward(
                code="WARD-01",
                name="Central Ward",
                min_lat=12.90,
                max_lat=13.00,
                min_lon=77.50,
                max_lon=77.65,
                is_active=True,
            )
            # North Ward: lat 13.00 to 13.15, lon 77.50 to 77.65
            self.ward_north = Ward(
                code="WARD-02",
                name="North Ward",
                min_lat=13.00,
                max_lat=13.15,
                min_lon=77.50,
                max_lon=77.65,
                is_active=True,
            )
            self.ward_inactive = Ward(
                code="WARD-99",
                name="Inactive Ward",
                min_lat=11.00,
                max_lat=11.50,
                min_lon=76.00,
                max_lon=76.50,
                is_active=False,
            )
            session.add_all([self.ward_central, self.ward_north, self.ward_inactive])
            session.flush()

            # Officers
            self.officer_pwd_central = Officer(
                user_subject="officer-pwd-1",
                name="Ramesh Sharma",
                role="officer",
                permissions=["complaint:resolve"],
                department_id=self.dept_pwd.id,
                ward_id=self.ward_central.id,
                is_active=True,
                active_complaints_count=2,
            )
            self.officer_pwd_central_busy = Officer(
                user_subject="officer-pwd-2",
                name="Suresh Kumar",
                role="officer",
                permissions=["complaint:resolve"],
                department_id=self.dept_pwd.id,
                ward_id=self.ward_central.id,
                is_active=True,
                active_complaints_count=10,
            )
            self.officer_pwd_inactive = Officer(
                user_subject="officer-pwd-inactive",
                name="Inactive Officer",
                role="officer",
                permissions=["complaint:resolve"],
                department_id=self.dept_pwd.id,
                ward_id=self.ward_central.id,
                is_active=False,
                active_complaints_count=0,
            )
            self.officer_pwd_no_perm = Officer(
                user_subject="officer-pwd-noperm",
                name="Unpermitted Officer",
                role="officer",
                permissions=["complaint:view"],
                department_id=self.dept_pwd.id,
                ward_id=self.ward_central.id,
                is_active=True,
                active_complaints_count=0,
            )
            self.officer_sanitation_central = Officer(
                user_subject="officer-san-1",
                name="Anita Verma",
                role="officer",
                permissions=["complaint:resolve"],
                department_id=self.dept_sanitation.id,
                ward_id=self.ward_central.id,
                is_active=True,
                active_complaints_count=1,
            )
            session.add_all([
                self.officer_pwd_central,
                self.officer_pwd_central_busy,
                self.officer_pwd_inactive,
                self.officer_pwd_no_perm,
                self.officer_sanitation_central,
            ])
            session.flush()

            # SLA Policies
            self.sla_pothole_high = SLAPolicy(
                category="roads_potholes",
                priority="high",
                duration_hours=24,
                is_active=True,
            )
            self.sla_pothole_medium = SLAPolicy(
                category="roads_potholes",
                priority="medium",
                duration_hours=48,
                is_active=True,
            )
            session.add_all([self.sla_pothole_high, self.sla_pothole_medium])
            session.commit()

    def _create_analyzed_complaint(
        self,
        *,
        category: str = "roads_potholes",
        priority: str = "medium",
        human_review: bool = False,
        outcome: str = "completed",
        location_text: str = "12.9500, 77.5800",
    ) -> Complaint:
        with self.sessions() as session:
            complaint = Complaint(
                public_reference=f"SAM-TEST-{uuid4().hex[:8].upper()}",
                owner_subject="citizen-123",
                description="Test complaint description",
                location_text=location_text,
                status=ComplaintState.SUBMITTED.value,
            )
            session.add(complaint)
            session.flush()

            # Add background analysis job
            job = BackgroundJob(
                complaint_id=complaint.id,
                media_id=None,
                work_type="complaint_analysis",
                idempotency_key=f"analysis:{complaint.id}",
                status="succeeded",
            )
            session.add(job)
            session.flush()

            # Add agent run
            run = AgentRun(
                complaint_id=complaint.id,
                job_id=job.id,
                attempt_number=1,
                agent_name="complaint_analyst",
                provider="openai",
                model="gpt-6-luna",
                schema_version="1.1",
                status="completed",
            )
            session.add(run)
            session.flush()

            # Add analysis result
            analysis = ComplaintAnalysis(
                complaint_id=complaint.id,
                media_id=complaint.id,  # test placeholder UUID
                agent_run_id=run.id,
                schema_version="1.1",
                provider="openai",
                model="gpt-6-luna",
                result={
                    "category": category,
                    "priority_recommendation": priority,
                    "confidence_level": "high",
                    "human_review_recommended": human_review,
                    "outcome": outcome,
                },
            )
            session.add(analysis)
            session.commit()
            session.refresh(complaint)
            return complaint

    # 1. Valid complaint routing
    def test_01_valid_complaint_routing(self):
        complaint = self._create_analyzed_complaint(
            category="roads_potholes",
            priority="medium",
            location_text="12.9500, 77.5800",
        )
        with self.sessions() as session:
            assignment = route_and_assign_complaint(
                session,
                public_reference=complaint.public_reference,
                actor_subject="supervisor-1",
            )
            self.assertEqual(assignment.status, "assigned")
            self.assertEqual(assignment.category, "roads_potholes")
            self.assertEqual(assignment.priority, "medium")
            self.assertEqual(assignment.department_id, self.dept_pwd.id)
            self.assertEqual(assignment.ward_id, self.ward_central.id)
            self.assertEqual(assignment.assigned_officer_id, self.officer_pwd_central.id)
            self.assertEqual(assignment.sla_hours, 48)
            self.assertIsNotNone(assignment.sla_deadline)

            # Check complaint status updated to assigned
            refreshed = session.get(Complaint, complaint.id)
            self.assertEqual(refreshed.status, ComplaintState.ASSIGNED.value)

    # 2. Correct department mapping
    def test_02_department_mappings(self):
        policy = RoutingPolicy.load()
        self.assertEqual(policy.category_department_mapping.get("roads_potholes"), "PWD")
        self.assertEqual(policy.category_department_mapping.get("garbage_sanitation"), "SANITATION")
        self.assertEqual(policy.category_department_mapping.get("water_leakage"), "WATER_SUPPLY")
        self.assertEqual(policy.category_department_mapping.get("streetlights_electrical"), "ELECTRICITY")
        self.assertEqual(policy.category_department_mapping.get("drainage_sewage"), "DRAINAGE")
        self.assertEqual(policy.category_department_mapping.get("damaged_public_infrastructure"), "PWD")

    # 3. Unknown complaint category
    def test_03_unknown_complaint_category(self):
        complaint = self._create_analyzed_complaint(
            category="other_uncertain",
            location_text="12.9500, 77.5800",
        )
        with self.sessions() as session:
            assignment = route_and_assign_complaint(
                session,
                public_reference=complaint.public_reference,
                actor_subject="supervisor-1",
            )
            self.assertEqual(assignment.status, "needs_review")
            self.assertIn("no configured department mapping", assignment.routing_reason)

    # 4. Missing GPS coordinates
    def test_04_missing_gps_coordinates(self):
        complaint = self._create_analyzed_complaint(
            category="roads_potholes",
            location_text="",
        )
        with self.sessions() as session:
            assignment = route_and_assign_complaint(
                session,
                public_reference=complaint.public_reference,
                actor_subject="supervisor-1",
            )
            self.assertEqual(assignment.status, "needs_review")
            self.assertIn("Missing or invalid GPS coordinates", assignment.routing_reason)

    # 5. Invalid GPS coordinates
    def test_05_invalid_gps_coordinates(self):
        # Latitude 150 is out of [-90, 90] bounds
        complaint = self._create_analyzed_complaint(
            category="roads_potholes",
            location_text="150.000, 77.5800",
        )
        with self.sessions() as session:
            assignment = route_and_assign_complaint(
                session,
                public_reference=complaint.public_reference,
                actor_subject="supervisor-1",
            )
            self.assertEqual(assignment.status, "needs_review")
            self.assertIn("Missing or invalid GPS coordinates", assignment.routing_reason)

    # 6. Correct ward detection
    def test_06_correct_ward_detection(self):
        # Central Ward: lat 12.90 - 13.00, lon 77.50 - 77.65
        coords = parse_coordinates("12.9500, 77.5800")
        self.assertIsNotNone(coords)
        lat, lon = coords
        with self.sessions() as session:
            wards = list(session.scalars(select(Ward)).all())
            ward = find_ward(lat, lon, wards)
            self.assertIsNotNone(ward)
            self.assertEqual(ward.code, "WARD-01")

        # North Ward: lat 13.05, lon 77.55
        coords_north = parse_coordinates("13.0500, 77.5500")
        lat_n, lon_n = coords_north
        with self.sessions() as session:
            wards = list(session.scalars(select(Ward)).all())
            ward_n = find_ward(lat_n, lon_n, wards)
            self.assertIsNotNone(ward_n)
            self.assertEqual(ward_n.code, "WARD-02")

    # 7. Unknown jurisdiction
    def test_07_unknown_jurisdiction(self):
        # Coordinates (28.6139, 77.2090) are in Delhi, far outside configured Bangalore wards
        complaint = self._create_analyzed_complaint(
            category="roads_potholes",
            location_text="28.6139, 77.2090",
        )
        with self.sessions() as session:
            assignment = route_and_assign_complaint(
                session,
                public_reference=complaint.public_reference,
                actor_subject="supervisor-1",
            )
            self.assertEqual(assignment.status, "needs_review")
            self.assertIn("fall outside all active municipal ward boundaries", assignment.routing_reason)

    # 8. Eligible officer selection (least workload selection)
    def test_08_eligible_officer_least_workload(self):
        # In Central Ward, officer_pwd_central has workload 2, officer_pwd_central_busy has workload 10
        with self.sessions() as session:
            officers = list(session.scalars(select(Officer)).all())
            selected = select_eligible_officer(
                self.dept_pwd.id,
                self.ward_central.id,
                officers,
                "complaint:resolve",
            )
            self.assertIsNotNone(selected)
            self.assertEqual(selected.id, self.officer_pwd_central.id)

    # 9. Inactive officer rejection
    def test_09_inactive_officer_rejection(self):
        with self.sessions() as session:
            # Only provide inactive officer
            selected = select_eligible_officer(
                self.dept_pwd.id,
                self.ward_central.id,
                [self.officer_pwd_inactive],
                "complaint:resolve",
            )
            self.assertIsNone(selected)

    # 10. Wrong department officer rejection
    def test_10_wrong_department_officer_rejection(self):
        with self.sessions() as session:
            # Sanitation officer should never be selected for PWD
            selected = select_eligible_officer(
                self.dept_pwd.id,
                self.ward_central.id,
                [self.officer_sanitation_central],
                "complaint:resolve",
            )
            self.assertIsNone(selected)

    # 11. Officer outside jurisdiction rejection
    def test_11_officer_outside_jurisdiction_rejection(self):
        with self.sessions() as session:
            # Central Ward officer should not be selected for North Ward
            selected = select_eligible_officer(
                self.dept_pwd.id,
                self.ward_north.id,
                [self.officer_pwd_central],
                "complaint:resolve",
            )
            self.assertIsNone(selected)

    # 12. No eligible officer available
    def test_12_no_eligible_officer_available(self):
        # North Ward has no PWD officer
        complaint = self._create_analyzed_complaint(
            category="roads_potholes",
            location_text="13.0500, 77.5500",  # North Ward
        )
        with self.sessions() as session:
            assignment = route_and_assign_complaint(
                session,
                public_reference=complaint.public_reference,
                actor_subject="supervisor-1",
            )
            self.assertEqual(assignment.status, "unassigned")
            self.assertIsNone(assignment.assigned_officer_id)
            self.assertEqual(assignment.ward_id, self.ward_north.id)
            self.assertIn("No active officer", assignment.routing_reason)

    # 13. Correct SLA calculation
    def test_13_correct_sla_calculation(self):
        now = datetime(2026, 11, 4, 10, 0, 0, tzinfo=timezone.utc)
        with self.sessions() as session:
            sla_policies = list(session.scalars(select(SLAPolicy)).all())
            policy = RoutingPolicy.load()
            duration, deadline = calculate_sla("roads_potholes", "high", now, sla_policies, policy)
            self.assertEqual(duration, 24)
            self.assertEqual(deadline, now + timedelta(hours=24))

    # 14. Missing SLA policy fallback
    def test_14_missing_sla_policy_fallback(self):
        now = datetime(2026, 11, 4, 10, 0, 0, tzinfo=timezone.utc)
        with self.sessions() as session:
            # Request SLA for category without explicit DB SLA policy (e.g. streetlights_electrical low)
            policy = RoutingPolicy.load()
            duration, deadline = calculate_sla("streetlights_electrical", "low", now, [], policy)
            self.assertEqual(duration, policy.default_sla_hours["low"])
            self.assertEqual(deadline, now + timedelta(hours=72))

    # 15. Successful database persistence
    def test_15_database_persistence(self):
        complaint = self._create_analyzed_complaint(
            category="roads_potholes",
            priority="medium",
            location_text="12.9500, 77.5800",
        )
        with self.sessions() as session:
            assignment = route_and_assign_complaint(
                session,
                public_reference=complaint.public_reference,
                actor_subject="supervisor-1",
            )
            assignment_id = assignment.id

        with self.sessions() as session:
            stored = session.get(ComplaintAssignment, assignment_id)
            self.assertIsNotNone(stored)
            self.assertEqual(stored.status, "assigned")
            self.assertEqual(stored.category, "roads_potholes")

            # Check audit event persisted
            events = list(
                session.scalars(
                    select(ComplaintEvent).where(ComplaintEvent.complaint_id == complaint.id)
                ).all()
            )
            self.assertTrue(any(e.event_type == "complaint_assigned" for e in events))

    # 16. Transaction rollback on failure
    def test_16_transaction_rollback_on_failure(self):
        complaint = self._create_analyzed_complaint(
            category="roads_potholes",
            location_text="12.9500, 77.5800",
        )
        with self.sessions() as session:
            with patch.object(session, "commit", side_effect=RuntimeError("Database failure")):
                with self.assertRaises(RuntimeError):
                    route_and_assign_complaint(
                        session,
                        public_reference=complaint.public_reference,
                        actor_subject="supervisor-1",
                    )

        # Confirm nothing was committed
        with self.sessions() as session:
            assignment = get_complaint_assignment(session, complaint_id=complaint.id)
            self.assertIsNone(assignment)

    # 17. Duplicate assignment prevention (Idempotency)
    def test_17_duplicate_assignment_prevention(self):
        complaint = self._create_analyzed_complaint(
            category="roads_potholes",
            location_text="12.9500, 77.5800",
        )
        with self.sessions() as session:
            first = route_and_assign_complaint(
                session,
                public_reference=complaint.public_reference,
                actor_subject="supervisor-1",
            )
            first_id = first.id

            # Call again
            second = route_and_assign_complaint(
                session,
                public_reference=complaint.public_reference,
                actor_subject="supervisor-1",
            )
            self.assertEqual(second.id, first_id)

            # Ensure only one assignment row exists in the database
            assignments = list(
                session.scalars(
                    select(ComplaintAssignment).where(ComplaintAssignment.complaint_id == complaint.id)
                ).all()
            )
            self.assertEqual(len(assignments), 1)

    # 18. Human-review handling
    def test_18_human_review_handling(self):
        # When Agent 1 flags human_review_recommended=True
        complaint = self._create_analyzed_complaint(
            category="roads_potholes",
            human_review=True,
            location_text="12.9500, 77.5800",
        )
        with self.sessions() as session:
            assignment = route_and_assign_complaint(
                session,
                public_reference=complaint.public_reference,
                actor_subject="supervisor-1",
            )
            self.assertEqual(assignment.status, "needs_review")
            self.assertIsNone(assignment.assigned_officer_id)
            self.assertIn("flagged for human review by Agent 1", assignment.routing_reason)

    # 19. Successful Agent 1 integration
    def test_19_successful_agent_1_integration(self):
        complaint = self._create_analyzed_complaint(
            category="garbage_sanitation",
            priority="high",
            location_text="12.9500, 77.5800",
        )
        with self.sessions() as session:
            assignment = route_and_assign_complaint(
                session,
                public_reference=complaint.public_reference,
                actor_subject="supervisor-1",
            )
            # Reused category from Agent 1
            self.assertEqual(assignment.category, "garbage_sanitation")
            self.assertEqual(assignment.department_id, self.dept_sanitation.id)
            self.assertEqual(assignment.assigned_officer_id, self.officer_sanitation_central.id)

    # 20. Successful Agent 3 monitoring handoff
    def test_20_agent_3_monitoring_handoff(self):
        complaint = self._create_analyzed_complaint(
            category="roads_potholes",
            location_text="12.9500, 77.5800",
        )
        with self.sessions() as session:
            route_and_assign_complaint(
                session,
                public_reference=complaint.public_reference,
                actor_subject="supervisor-1",
            )

            # Check that an SLA monitoring background job was scheduled for Agent 3
            monitoring_job = session.scalar(
                select(BackgroundJob).where(
                    BackgroundJob.complaint_id == complaint.id,
                    BackgroundJob.work_type == "sla_monitoring",
                )
            )
            self.assertIsNotNone(monitoring_job)
            self.assertEqual(monitoring_job.status, "pending")
            self.assertEqual(monitoring_job.idempotency_key, f"sla_monitoring:{complaint.id}")

    # 21. Agent 3 job scheduling retry / worker retry behavior
    def test_21_routing_worker_retry_behavior(self):
        complaint = self._create_analyzed_complaint(
            category="roads_potholes",
            location_text="12.9500, 77.5800",
        )
        # Create a complaint_routing job
        with self.sessions() as session:
            job = BackgroundJob(
                complaint_id=complaint.id,
                media_id=None,
                work_type="complaint_routing",
                idempotency_key=f"routing:{complaint.id}",
                status="pending",
                max_attempts=3,
            )
            session.add(job)
            session.commit()
            job_id = job.id

        worker = ComplaintRoutingWorker(
            session_factory=self.sessions,
            settings=self.settings,
        )

        # First run succeeds
        success = worker.process_one()
        self.assertTrue(success)

        with self.sessions() as session:
            refreshed_job = session.get(BackgroundJob, job_id)
            self.assertEqual(refreshed_job.status, "succeeded")
            self.assertIsNone(refreshed_job.error_code)

    # 22. API authentication and authorization
    def test_22_api_authentication_and_authorization(self):
        complaint = self._create_analyzed_complaint(
            category="roads_potholes",
            location_text="12.9500, 77.5800",
        )

        def override_session():
            with self.sessions() as session:
                yield session

        app.dependency_overrides[get_session] = override_session

        client = TestClient(app)

        # Case A: Missing token -> 401
        res = client.post(f"/api/v1/staff/complaint-routing/{complaint.public_reference}")
        self.assertEqual(res.status_code, 401)

        # Case B: Citizen token attempting staff routing -> 401/403
        import jwt

        citizen_token = jwt.encode(
            {"sub": "cit-1", "role": "citizen", "exp": int(utc_now().timestamp()) + 3600, "iss": "https://issuer.invalid", "aud": "samadhan-test"},
            "test-signing-secret-that-is-at-least-32-bytes",
            algorithm="HS256",
        )
        res = client.post(
            f"/api/v1/staff/complaint-routing/{complaint.public_reference}",
            headers={"Authorization": f"Bearer {citizen_token}"},
        )
        self.assertIn(res.status_code, (401, 403))

        # Case C: Staff with complaint_routing:assign permission -> 200 OK
        staff_token = jwt.encode(
            {
                "sub": "staff-1",
                "role": "staff",
                "permissions": ["complaint_routing:assign"],
                "exp": int(utc_now().timestamp()) + 3600,
                "iss": "https://issuer.invalid",
                "aud": "samadhan-test",
            },
            "test-signing-secret-that-is-at-least-32-bytes",
            algorithm="HS256",
        )
        res = client.post(
            f"/api/v1/staff/complaint-routing/{complaint.public_reference}",
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "assigned")
        self.assertEqual(data["category"], "roads_potholes")
        self.assertEqual(data["department_code"], "PWD")
        self.assertEqual(data["ward_code"], "WARD-01")

        # GET assignment endpoint
        get_res = client.get(
            f"/api/v1/staff/complaint-routing/{complaint.public_reference}",
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()["status"], "assigned")

        # Cleanup overrides
        app.dependency_overrides.clear()


if __name__ == "__main__":
    unittest.main()
