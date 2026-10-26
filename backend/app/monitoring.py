"""Application integration points for Agent 2 and resolution workflows."""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.models import MonitoringCase


class MonitoringRegistrationError(ValueError):
    pass


def register_monitoring_case(
    session: Session,
    *,
    complaint_id: UUID,
    complaint_reference: str,
    jurisdiction_id: str,
    department_id: str,
    assigned_officer_subject: str,
    sla_policy_id: str,
    sla_policy_version: str,
    sla_deadline_at: datetime,
) -> MonitoringCase:
    """Persist Agent 2's already-validated SLA assignment for Agent 3 to monitor.

    Call this in the same transaction that persists the validated ticket routing.
    This function does not choose or calculate an SLA.
    """
    if sla_deadline_at.tzinfo is None or sla_deadline_at.utcoffset() is None:
        raise MonitoringRegistrationError("SLA deadline must be timezone-aware.")
    if not all((jurisdiction_id, department_id, assigned_officer_subject, sla_policy_id, sla_policy_version)):
        raise MonitoringRegistrationError("Routing and versioned SLA references are required.")
    case = MonitoringCase(
        complaint_id=complaint_id,
        complaint_reference=complaint_reference,
        jurisdiction_id=jurisdiction_id,
        department_id=department_id,
        assigned_officer_subject=assigned_officer_subject,
        sla_policy_id=sla_policy_id,
        sla_policy_version=sla_policy_version,
        sla_deadline_at=sla_deadline_at.astimezone(timezone.utc),
        work_status="assigned",
        sla_status="active",
        escalation_status="none",
        verification_status="not_started",
    )
    session.add(case)
    session.flush()
    return case


def record_resolution_submission(
    session: Session,
    *,
    complaint_id: UUID,
    actor_subject: str,
    evidence_ref: str,
    verification_deadline_at: datetime,
    submitted_at: datetime | None = None,
) -> MonitoringCase:
    """Record officer completion; the monitor starts citizen verification on its next scan."""
    case = session.query(MonitoringCase).filter_by(complaint_id=complaint_id).with_for_update().one_or_none()
    if case is None:
        raise MonitoringRegistrationError("No monitoring record exists for the complaint.")
    if case.assigned_officer_subject != actor_subject:
        raise MonitoringRegistrationError("Only the assigned officer may submit resolution proof.")
    if not evidence_ref.strip():
        raise MonitoringRegistrationError("A private evidence reference is required.")
    if case.work_status not in {"assigned", "in_progress"}:
        raise MonitoringRegistrationError("The work item is not in a resolvable state.")
    now = submitted_at or datetime.now(timezone.utc)
    if now.tzinfo is None or now.utcoffset() is None or verification_deadline_at.tzinfo is None or verification_deadline_at.utcoffset() is None:
        raise MonitoringRegistrationError("Submission and verification deadlines must be timezone-aware.")
    now = now.astimezone(timezone.utc)
    deadline = verification_deadline_at.astimezone(timezone.utc)
    if deadline <= now:
        raise MonitoringRegistrationError("Verification deadline must be in the future.")
    case.work_status = "resolution_submitted"
    case.work_completed_at = now
    case.resolution_evidence_ref = evidence_ref
    case.verification_status = "not_started"
    case.verification_deadline_at = deadline
    session.flush()
    return case





