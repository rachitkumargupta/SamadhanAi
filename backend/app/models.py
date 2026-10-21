from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
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
