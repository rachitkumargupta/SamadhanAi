from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Complaint(Base):
    __tablename__ = "complaints"
    __table_args__ = (Index("ix_complaints_owner_created", "owner_subject", "created_at"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    public_reference: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    owner_subject: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location_text: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="submitted")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    events: Mapped[list["ComplaintEvent"]] = relationship(
        back_populates="complaint"
    )
    media: Mapped[list["ComplaintMedia"]] = relationship(back_populates="complaint")


class ComplaintMedia(Base):
    __tablename__ = "complaint_media"
    __table_args__ = (
        Index("ix_complaint_media_complaint_created", "complaint_id", "created_at"),
        CheckConstraint("size_bytes > 0", name="ck_complaint_media_positive_size"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    complaint_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("complaints.id", ondelete="RESTRICT"), nullable=False
    )
    object_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    media_type: Mapped[str] = mapped_column(String(80), nullable=False)
    purpose: Mapped[str] = mapped_column(String(40), nullable=False, default="complaint_image")
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    uploaded_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    complaint: Mapped[Complaint] = relationship(back_populates="media")


class BackgroundJob(Base):
    __tablename__ = "background_jobs"
    __table_args__ = (
        Index("ix_background_jobs_claim", "status", "available_at", "lease_expires_at"),
        CheckConstraint(
            "status IN ('pending', 'running', 'succeeded', 'failed')",
            name="ck_background_jobs_status",
        ),
        CheckConstraint(
            "attempt_count >= 0 AND max_attempts > 0 AND attempt_count <= max_attempts",
            name="ck_background_jobs_attempts",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    complaint_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("complaints.id", ondelete="RESTRICT"), nullable=False
    )
    media_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("complaint_media.id", ondelete="RESTRICT"), nullable=False
    )
    work_type: Mapped[str] = mapped_column(String(80), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")
    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    lease_owner: Mapped[str | None] = mapped_column(String(120), nullable=True)
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AgentRun(Base):
    __tablename__ = "agent_runs"
    __table_args__ = (
        Index("ix_agent_runs_complaint_started", "complaint_id", "started_at"),
        UniqueConstraint("job_id", "attempt_number", name="uq_agent_runs_job_attempt"),
        CheckConstraint("attempt_number > 0", name="ck_agent_runs_attempt_number"),
        CheckConstraint(
            "status IN ('running', 'completed', 'failed', 'abandoned')",
            name="ck_agent_runs_status",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    complaint_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("complaints.id", ondelete="RESTRICT"), nullable=False
    )
    job_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("background_jobs.id", ondelete="RESTRICT"), nullable=False
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    agent_name: Mapped[str] = mapped_column(String(80), nullable=False)
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    model: Mapped[str] = mapped_column(String(160), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ComplaintAnalysis(Base):
    __tablename__ = "complaint_analysis"
    __table_args__ = (Index("ix_complaint_analysis_complaint_created", "complaint_id", "created_at"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    complaint_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("complaints.id", ondelete="RESTRICT"), nullable=False
    )
    media_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("complaint_media.id", ondelete="RESTRICT"), nullable=False
    )
    agent_run_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("agent_runs.id", ondelete="RESTRICT"), nullable=False
    )
    schema_version: Mapped[str] = mapped_column(String(40), nullable=False)
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    model: Mapped[str] = mapped_column(String(160), nullable=False)
    result: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ComplaintEvent(Base):
    __tablename__ = "complaint_events"
    __table_args__ = (Index("ix_complaint_events_complaint_time", "complaint_id", "occurred_at"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    complaint_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("complaints.id", ondelete="RESTRICT"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    actor_subject: Mapped[str] = mapped_column(String(255), nullable=False)
    previous_state: Mapped[str | None] = mapped_column(String(40), nullable=True)
    resulting_state: Mapped[str | None] = mapped_column(String(40), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    visibility: Mapped[str] = mapped_column(
        String(20), nullable=False, default="internal", server_default="internal"
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    complaint: Mapped[Complaint] = relationship(back_populates="events")


class MonitoringCase(Base):
    """Agent 3's monitoring projection, populated by application/Agent 2 workflows."""
    __tablename__ = "monitoring_cases"
    __table_args__ = (
        UniqueConstraint("complaint_id", name="uq_monitoring_case_complaint"),
        Index("ix_monitoring_cases_sla_due", "sla_status", "sla_deadline_at"),
        Index("ix_monitoring_cases_verification_due", "verification_status", "verification_deadline_at"),
        CheckConstraint("work_status IN ('assigned', 'in_progress', 'resolution_submitted', 'pending_citizen_verification', 'disputed', 'closed')", name="ck_monitoring_case_work_status"),
        CheckConstraint("verification_status IN ('not_started', 'pending_citizen', 'review_required', 'approved', 'disputed')", name="ck_monitoring_case_verification_status"),
        CheckConstraint("sla_status IN ('active', 'met', 'breached')", name="ck_monitoring_case_sla_status"),
        CheckConstraint("escalation_status IN ('none', 'open', 'closed')", name="ck_monitoring_case_escalation_status"),
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    complaint_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("complaints.id", ondelete="RESTRICT"), nullable=False)
    complaint_reference: Mapped[str] = mapped_column(String(32), nullable=False)
    jurisdiction_id: Mapped[str] = mapped_column(String(100), nullable=False)
    department_id: Mapped[str] = mapped_column(String(100), nullable=False)
    assigned_officer_subject: Mapped[str] = mapped_column(String(255), nullable=False)
    senior_authority_subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    current_escalation_level: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    independent_reviewer_subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sla_policy_id: Mapped[str] = mapped_column(String(100), nullable=False)
    sla_policy_version: Mapped[str] = mapped_column(String(64), nullable=False)
    sla_deadline_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sla_status: Mapped[str] = mapped_column(String(24), nullable=False, default="active")
    work_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sla_breached_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    work_status: Mapped[str] = mapped_column(String(48), nullable=False, default="assigned")
    escalation_status: Mapped[str] = mapped_column(String(24), nullable=False, default="none")
    verification_status: Mapped[str] = mapped_column(String(32), nullable=False, default="not_started")
    verification_deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_evidence_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    verification_routed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)


class MonitoringAuthority(Base):
    """Configured eligible authority hierarchy; values come from approved reference data."""
    __tablename__ = "monitoring_authorities"
    __table_args__ = (
        Index("ix_monitoring_authorities_lookup", "jurisdiction_id", "department_id", "authority_type", "active"),
        CheckConstraint("authority_type IN ('senior_authority', 'independent_reviewer')", name="ck_monitoring_authority_type"),
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    subject: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    authority_type: Mapped[str] = mapped_column(String(40), nullable=False)
    jurisdiction_id: Mapped[str] = mapped_column(String(100), nullable=False)
    department_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    escalation_level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    eligibility_basis: Mapped[str] = mapped_column(String(300), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class MonitoringEvent(Base):
    __tablename__ = "monitoring_events"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_monitoring_event_idempotency"),
        Index("ix_monitoring_events_case_time", "monitoring_case_id", "occurred_at"),
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    monitoring_case_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("monitoring_cases.id", ondelete="RESTRICT"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class MonitoringJob(Base):
    __tablename__ = "monitoring_jobs"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_monitoring_job_idempotency"),
        Index("ix_monitoring_jobs_claim", "status", "available_at", "lease_expires_at"),
        CheckConstraint("status IN ('pending', 'running', 'succeeded', 'failed')", name="ck_monitoring_job_status"),
        CheckConstraint("attempt_count >= 0 AND max_attempts > 0", name="ck_monitoring_job_attempts"),
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    monitoring_case_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("monitoring_cases.id", ondelete="RESTRICT"), nullable=False)
    event_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("monitoring_events.id", ondelete="RESTRICT"), nullable=False)
    job_type: Mapped[str] = mapped_column(String(80), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    lease_owner: Mapped[str | None] = mapped_column(String(120), nullable=True)
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MonitoringNotification(Base):
    __tablename__ = "monitoring_notifications"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_monitoring_notification_idempotency"),
        Index("ix_monitoring_notifications_recipient", "recipient_subject", "created_at"),
    )
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    monitoring_case_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("monitoring_cases.id", ondelete="RESTRICT"), nullable=False)
    recipient_subject: Mapped[str] = mapped_column(String(255), nullable=False)
    notification_type: Mapped[str] = mapped_column(String(80), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)






