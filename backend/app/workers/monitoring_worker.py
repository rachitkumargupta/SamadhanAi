"""Deterministic Agent 3 monitor plus event-triggered escalation reasoning.

The loop scans indexed deadline columns only. The LLM is called exclusively for
claimed ``agent3_sla_escalation`` jobs created with an SLA_BREACHED event.
Verification timeouts are handled deterministically and assigned to reviewers.
"""
from __future__ import annotations

import argparse
import logging
import socket
import time
from datetime import datetime, timedelta, timezone
from typing import Callable
from uuid import UUID, uuid4

from sqlalchemy import or_, select, update
from sqlalchemy.orm import Session, sessionmaker

from backend.app.agents.monitoring_escalation import (
    AuthorityCandidate,
    EscalationEvent,
    MonitoringEscalationAgent,
    build_monitoring_escalation_agent,
)
from backend.app.config import Settings, get_settings
from backend.app.database import SessionLocal
from backend.app.models import (
    Complaint,
    ComplaintEvent,
    MonitoringAuthority,
    MonitoringCase,
    MonitoringEvent,
    MonitoringJob,
    MonitoringNotification,
)

logger = logging.getLogger(__name__)
LEASE_SECONDS = 180
BATCH_SIZE = 100
MAX_RETRY_DELAY_SECONDS = 300


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MonitoringWorker:
    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        agent_factory: Callable[[], MonitoringEscalationAgent],
        settings: Settings,
        worker_id: str | None = None,
    ):
        self._session_factory = session_factory
        self._agent_factory = agent_factory
        self._settings = settings
        self._worker_id = worker_id or f"{socket.gethostname()[:60]}:{uuid4().hex[:12]}"

    def scan_due_sla_cases(self, *, now: datetime | None = None) -> int:
        instant = now or utc_now()
        created = 0
        with self._session_factory() as session:
            cases = list(session.scalars(
                select(MonitoringCase)
                .where(
                    MonitoringCase.sla_status == "active",
                    MonitoringCase.sla_deadline_at <= instant,
                    MonitoringCase.sla_breached_at.is_(None),
                )
                .order_by(MonitoringCase.sla_deadline_at, MonitoringCase.id)
                .with_for_update(skip_locked=True)
                .limit(BATCH_SIZE)
            ).all())
            for case in cases:
                # Re-read under the row lock. A completion that won the race is not breached.
                if case.sla_status != "active" or case.sla_deadline_at > instant:
                    continue
                if case.work_completed_at is not None and case.work_completed_at <= case.sla_deadline_at:
                    case.sla_status = "met"
                    continue
                case.sla_status = "breached"
                case.sla_breached_at = instant
                case.escalation_status = "open"
                event = MonitoringEvent(
                    monitoring_case_id=case.id,
                    event_type="SLA_BREACHED",
                    idempotency_key=f"sla-breach:{case.id}:{case.sla_policy_id}:{case.sla_policy_version}",
                    data={
                        "sla_policy_id": case.sla_policy_id,
                        "sla_policy_version": case.sla_policy_version,
                        "deadline_at": case.sla_deadline_at.isoformat(),
                    },
                    occurred_at=instant,
                )
                session.add(event)
                session.flush()
                session.add(MonitoringJob(
                    monitoring_case_id=case.id,
                    event_id=event.id,
                    job_type="agent3_sla_escalation",
                    idempotency_key=f"agent3-sla-escalation:{event.id}",
                    status="pending",
                    available_at=instant,
                    max_attempts=5,
                ))
                created += 1
            session.commit()
        return created

    def start_citizen_verification(self, *, now: datetime | None = None) -> int:
        """Move officer-submitted proof into citizen verification and queue notice."""
        instant = now or utc_now()
        started = 0
        with self._session_factory() as session:
            cases = list(session.scalars(
                select(MonitoringCase)
                .where(
                    MonitoringCase.work_status == "resolution_submitted",
                    MonitoringCase.verification_status == "not_started",
                    MonitoringCase.resolution_evidence_ref.is_not(None),
                    MonitoringCase.verification_deadline_at.is_not(None),
                )
                .order_by(MonitoringCase.work_completed_at, MonitoringCase.id)
                .with_for_update(skip_locked=True)
                .limit(BATCH_SIZE)
            ).all())
            for case in cases:
                complaint = session.get(Complaint, case.complaint_id)
                if complaint is None:
                    logger.error("Cannot start citizen verification; complaint missing case=%s", case.complaint_reference)
                    continue
                case.work_status = "pending_citizen_verification"
                case.verification_status = "pending_citizen"
                submitted_at = case.work_completed_at or instant
                session.add(MonitoringEvent(
                    monitoring_case_id=case.id,
                    event_type="CITIZEN_VERIFICATION_STARTED",
                    idempotency_key=f"citizen-verification-start:{case.id}:{submitted_at.isoformat()}",
                    data={
                        "verification_deadline_at": case.verification_deadline_at.isoformat(),
                        "evidence_available": True,
                        "proof_url": f"/api/v1/complaints/{case.complaint_reference}/verification-proof",
                    },
                    occurred_at=instant,
                ))
                session.add(MonitoringNotification(
                    monitoring_case_id=case.id,
                    recipient_subject=complaint.owner_subject,
                    notification_type="citizen_verification_requested",
                    idempotency_key=f"citizen-verification-notice:{case.id}:{submitted_at.isoformat()}",
                    payload={
                        "complaint_reference": case.complaint_reference,
                        "verification_deadline_at": case.verification_deadline_at.isoformat(),
                        "evidence_available": True,
                        "proof_url": f"/api/v1/complaints/{case.complaint_reference}/verification-proof",
                    },
                    created_at=instant,
                ))
                started += 1
            session.commit()
        return started
    def route_due_verifications(self, *, now: datetime | None = None) -> int:
        """Route citizen silence to an independent reviewer; never call the LLM."""
        instant = now or utc_now()
        routed = 0
        with self._session_factory() as session:
            cases = list(session.scalars(
                select(MonitoringCase)
                .where(or_(
                    (MonitoringCase.verification_status == "pending_citizen")
                    & (MonitoringCase.verification_deadline_at <= instant)
                    & MonitoringCase.verification_routed_at.is_(None),
                    (MonitoringCase.verification_status == "review_required")
                    & MonitoringCase.independent_reviewer_subject.is_(None),
                ))
                .order_by(MonitoringCase.verification_deadline_at, MonitoringCase.id)
                .with_for_update(skip_locked=True)
                .limit(BATCH_SIZE)
            ).all())
            for case in cases:
                reviewer = session.scalar(
                    select(MonitoringAuthority)
                    .where(
                        MonitoringAuthority.active.is_(True),
                        MonitoringAuthority.authority_type == "independent_reviewer",
                        MonitoringAuthority.jurisdiction_id == case.jurisdiction_id,
                        MonitoringAuthority.department_id.is_(None),
                    )
                    .order_by(MonitoringAuthority.escalation_level, MonitoringAuthority.id)
                    .limit(1)
                )
                is_first_handoff = case.verification_status == "pending_citizen"
                if is_first_handoff:
                    case.verification_status = "review_required"
                    case.verification_routed_at = instant
                if reviewer is not None:
                    case.independent_reviewer_subject = reviewer.subject
                    event_type = "VERIFICATION_OVERDUE" if is_first_handoff else "VERIFICATION_REVIEWER_ASSIGNED"
                    session.add(MonitoringEvent(
                        monitoring_case_id=case.id,
                        event_type=event_type,
                        idempotency_key=f"verification-review-assignment:{case.id}:{case.verification_deadline_at.isoformat()}",
                        data={
                            "deadline_at": case.verification_deadline_at.isoformat(),
                            "reviewer_subject": reviewer.subject,
                        },
                        occurred_at=instant,
                    ))
                    session.add(MonitoringNotification(
                        monitoring_case_id=case.id,
                        recipient_subject=reviewer.subject,
                        notification_type="independent_verification_review_required",
                        idempotency_key=f"verification-review:{case.id}:{case.verification_deadline_at.isoformat()}",
                        payload={"complaint_reference": case.complaint_reference, "proof_url": f"/api/v1/staff/verification-reviews/{case.complaint_reference}/proof"},
                        created_at=instant,
                    ))
                elif is_first_handoff:
                    session.add(MonitoringEvent(
                        monitoring_case_id=case.id,
                        event_type="VERIFICATION_OVERDUE_REVIEWER_UNAVAILABLE",
                        idempotency_key=f"verification-reviewer-missing:{case.id}:{case.verification_deadline_at.isoformat()}",
                        data={"deadline_at": case.verification_deadline_at.isoformat()},
                        occurred_at=instant,
                    ))
                    logger.error("No independent reviewer configured for jurisdiction=%s case=%s", case.jurisdiction_id, case.complaint_reference)
                routed += 1
            session.commit()
        return routed
    def claim_one_job(self, *, now: datetime | None = None) -> UUID | None:
        instant = now or utc_now()
        with self._session_factory() as session:
            session.execute(update(MonitoringJob).where(MonitoringJob.status == "running", MonitoringJob.lease_expires_at <= instant, MonitoringJob.attempt_count >= MonitoringJob.max_attempts).values(status="failed", error_code="worker_attempts_exhausted", lease_owner=None, lease_expires_at=None, completed_at=instant))
            job = session.scalar(
                select(MonitoringJob)
                .where(
                    MonitoringJob.job_type == "agent3_sla_escalation",
                    MonitoringJob.attempt_count < MonitoringJob.max_attempts,
                    or_(
                        (MonitoringJob.status == "pending") & (MonitoringJob.available_at <= instant),
                        (MonitoringJob.status == "running") & (MonitoringJob.lease_expires_at <= instant),
                    ),
                )
                .order_by(MonitoringJob.available_at, MonitoringJob.created_at)
                .with_for_update(skip_locked=True)
                .limit(1)
            )
            if job is None:
                session.commit()
                return None
            job.status = "running"
            job.attempt_count += 1
            job.lease_owner = self._worker_id
            job.lease_expires_at = instant + timedelta(seconds=LEASE_SECONDS)
            session.commit()
            return job.id

    def process_one_agent_job(self) -> bool:
        job_id = self.claim_one_job()
        if job_id is None:
            return False

        with self._session_factory() as session:
            job = session.get(MonitoringJob, job_id)
            case = session.get(MonitoringCase, job.monitoring_case_id) if job else None
            event = session.get(MonitoringEvent, job.event_id) if job else None
            complaint = session.get(Complaint, case.complaint_id) if case else None
            if job is None or case is None or event is None or complaint is None or job.lease_owner != self._worker_id:
                if job is not None:
                    self._fail_job(session, job, "escalation_context_unavailable", retryable=False)
                    session.commit()
                return True
            authorities = list(session.scalars(
                select(MonitoringAuthority)
                .where(
                    MonitoringAuthority.active.is_(True),
                    MonitoringAuthority.authority_type == "senior_authority",
                    MonitoringAuthority.jurisdiction_id == case.jurisdiction_id,
                    MonitoringAuthority.escalation_level > case.current_escalation_level,
                    or_(MonitoringAuthority.department_id == case.department_id, MonitoringAuthority.department_id.is_(None)),
                )
                .order_by(MonitoringAuthority.escalation_level, MonitoringAuthority.id)
                .limit(20)
            ).all())
            history = list(session.scalars(
                select(ComplaintEvent)
                .where(ComplaintEvent.complaint_id == case.complaint_id)
                .order_by(ComplaintEvent.occurred_at.desc())
                .limit(39)
            ).all())
            prior = list(session.scalars(
                select(MonitoringEvent)
                .where(MonitoringEvent.monitoring_case_id == case.id, MonitoringEvent.event_type == "SLA_BREACHED", MonitoringEvent.id != event.id)
                .order_by(MonitoringEvent.occurred_at)
            ).all())
            payload = {
                "event_id": str(event.id),
                "complaint_reference": case.complaint_reference,
                "ticket_reference": case.complaint_reference,
                "ticket_state": case.work_status,
                "sla_policy_id": case.sla_policy_id,
                "sla_policy_version": case.sla_policy_version,
                "deadline_utc": case.sla_deadline_at.isoformat(),
                "breached_at_utc": (case.sla_breached_at or event.occurred_at).isoformat(),
                "authorities": authorities,
                "history": history,
                "prior": prior,
                "description": complaint.description,
                "location_text": complaint.location_text,
                "job_attempt": job.attempt_count,
            }
            session.commit()

        try:
            candidates = [AuthorityCandidate(
                authority_id=str(item.id),
                display_name=item.display_name,
                level=f"level_{item.escalation_level}",
                eligibility_basis=item.eligibility_basis,
            ) for item in payload["authorities"]]
            event_input = EscalationEvent(
                event_id=payload["event_id"],
                event_type="SLA_BREACHED",
                breach_confirmed=True,
                complaint_reference=payload["complaint_reference"],
                ticket_reference=payload["ticket_reference"],
                ticket_state=payload["ticket_state"],
                sla_policy_id=payload["sla_policy_id"],
                sla_policy_version=payload["sla_policy_version"],
                deadline_utc=payload["deadline_utc"],
                breached_at_utc=payload["breached_at_utc"],
                escalation_hierarchy=candidates,
                prior_escalations=[f"SLA_BREACHED at {row.occurred_at.isoformat()}" for row in payload["prior"]],
                notification_outcomes=[],
                case_history=(["Citizen report: " + str(payload["description"])[:900]] if payload["description"] else []) + [self._history_summary(row) for row in payload["history"]],
                unresolved_dependencies=[],
            )
            proposal = self._agent_factory().handle(event_input)
        except Exception as exc:
            with self._session_factory() as session:
                job = session.get(MonitoringJob, job_id)
                if job is not None and job.lease_owner == self._worker_id:
                    self._fail_job(session, job, f"agent3_failed_{type(exc).__name__}", retryable=True)
                    session.commit()
            return True

        with self._session_factory() as session:
            job = session.get(MonitoringJob, job_id)
            case = session.get(MonitoringCase, job.monitoring_case_id) if job else None
            if job is None or case is None or job.lease_owner != self._worker_id:
                return True
            job.result = proposal.model_dump(mode="json")
            job.status = "succeeded"
            job.lease_owner = None
            job.lease_expires_at = None
            job.completed_at = utc_now()
            job.error_code = None
            if proposal.recommended_authority_id:
                authority = session.get(MonitoringAuthority, UUID(proposal.recommended_authority_id))
                still_eligible = (
                    authority is not None
                    and authority.active
                    and authority.authority_type == "senior_authority"
                    and authority.jurisdiction_id == case.jurisdiction_id
                    and authority.escalation_level > case.current_escalation_level
                    and (authority.department_id == case.department_id or authority.department_id is None)
                )
                if still_eligible:
                    case.senior_authority_subject = authority.subject
                    case.current_escalation_level = authority.escalation_level
                    session.add(MonitoringNotification(
                        monitoring_case_id=case.id,
                        recipient_subject=authority.subject,
                        notification_type="sla_breach_escalation",
                        idempotency_key=f"sla-escalation-notification:{job.event_id}",
                        payload={
                            "complaint_reference": case.complaint_reference,
                            "brief": proposal.breach_summary,
                            "explanation": proposal.explanation,
                            "review_flags": proposal.review_flags,
                        },
                    ))
            session.add(MonitoringEvent(
                monitoring_case_id=case.id,
                event_type="AGENT3_ESCALATION_PROPOSAL_RECORDED",
                idempotency_key=f"agent3-proposal:{job.id}",
                data=proposal.model_dump(mode="json"),
            ))
            session.commit()
        return True

    @staticmethod
    def _history_summary(event: ComplaintEvent) -> str:
        # Do not pass private actor identifiers to the model.
        details = (event.reason or "").strip()
        return f"{event.event_type}: {details}"[:1000]

    def _fail_job(self, session: Session, job: MonitoringJob, code: str, *, retryable: bool) -> None:
        now = utc_now()
        can_retry = retryable and job.attempt_count < job.max_attempts
        if can_retry:
            job.status = "pending"
            job.available_at = now + timedelta(seconds=min(2 ** job.attempt_count, MAX_RETRY_DELAY_SECONDS))
        else:
            job.status = "failed"
            job.completed_at = now
        job.error_code = code
        job.lease_owner = None
        job.lease_expires_at = None
        logger.warning("Monitoring job %s finished with %s", job.id, code)

    def run_once(self) -> bool:
        started = self.start_citizen_verification()
        breached = self.scan_due_sla_cases()
        overdue = self.route_due_verifications()
        worked = self.process_one_agent_job()
        return bool(started or breached or overdue or worked)

    def run_forever(self) -> None:
        while True:
            try:
                did_work = self.run_once()
            except Exception as exc:
                logger.error("Monitoring worker iteration failed error_type=%s", type(exc).__name__)
                did_work = False
            if not did_work:
                time.sleep(self._settings.monitoring_worker_poll_seconds)


def create_worker(settings: Settings | None = None) -> MonitoringWorker:
    configured = settings or get_settings()
    return MonitoringWorker(
        session_factory=SessionLocal,
        agent_factory=lambda: build_monitoring_escalation_agent(configured),
        settings=configured,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the deterministic deadline monitor and Agent 3 worker")
    parser.add_argument("--once", action="store_true", help="scan deadlines and process at most one Agent 3 job")
    args = parser.parse_args()
    worker = create_worker()
    if args.once:
        worker.run_once()
    else:
        worker.run_forever()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()














