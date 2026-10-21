from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, Uuid, func
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
    description: Mapped[str] = mapped_column(Text, nullable=False)
    location_text: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="submitted")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    events: Mapped[list["ComplaintEvent"]] = relationship(
        back_populates="complaint"
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
