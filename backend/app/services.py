import secrets
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.domain.lifecycle import (
    ComplaintState,
    TransitionContext,
    validate_transition,
)
from backend.app.models import Complaint, ComplaintEvent
from backend.app.schemas import ComplaintCreate


def new_public_reference() -> str:
    return f"SAM-{secrets.token_urlsafe(12).replace('-', 'A').replace('_', 'B').upper()}"


def submit_complaint(
    session: Session,
    *,
    actor_subject: str,
    payload: ComplaintCreate,
    correlation_id: str,
) -> Complaint:
    complaint = Complaint(
        public_reference=new_public_reference(),
        owner_subject=actor_subject,
        description=payload.description,
        location_text=payload.location_text,
        status=ComplaintState.SUBMITTED.value,
    )
    session.add(complaint)
    session.flush()
    session.add(
        ComplaintEvent(
            complaint_id=complaint.id,
            event_type="complaint_registered",
            actor_subject=actor_subject,
            previous_state=None,
            resulting_state=ComplaintState.SUBMITTED.value,
            correlation_id=correlation_id,
            visibility="citizen",
        )
    )
    session.commit()
    session.refresh(complaint)
    return complaint


def get_owned_complaint(
    session: Session, *, public_reference: str, actor_subject: str
) -> Complaint | None:
    statement = select(Complaint).where(
        Complaint.public_reference == public_reference,
        Complaint.owner_subject == actor_subject,
    )
    return session.scalar(statement)


def list_owned_complaints(
    session: Session, *, actor_subject: str, offset: int, limit: int
) -> tuple[list[Complaint], bool]:
    statement = (
        select(Complaint)
        .where(Complaint.owner_subject == actor_subject)
        .order_by(Complaint.created_at.desc(), Complaint.id.desc())
        .offset(offset)
        .limit(limit + 1)
    )
    results = list(session.scalars(statement).all())
    has_more = len(results) > limit
    return results[:limit], has_more


def list_citizen_visible_events(
    session: Session,
    *,
    complaint_id: UUID,
    offset: int,
    limit: int,
) -> tuple[list[ComplaintEvent], bool]:
    statement = (
        select(ComplaintEvent)
        .where(
            ComplaintEvent.complaint_id == complaint_id,
            ComplaintEvent.visibility == "citizen",
        )
        .order_by(ComplaintEvent.occurred_at, ComplaintEvent.id)
        .offset(offset)
        .limit(limit + 1)
    )
    results = list(session.scalars(statement).all())
    has_more = len(results) > limit
    return results[:limit], has_more


def transition_complaint(
    session: Session,
    *,
    public_reference: str,
    context: TransitionContext,
    target_state: str,
    correlation_id: str | None = None,
    citizen_visible: bool = False,
) -> Complaint | None:
    """Apply a candidate transition and its audit event in one transaction.

    This internal operation is not exposed by an API route. Callers must build
    ``context`` from a verified actor and server-side ownership/assignment data;
    once an assignment model exists, its scope must be checked before calling.
    """

    complaint = session.scalar(
        select(Complaint)
        .where(Complaint.public_reference == public_reference)
        .with_for_update()
    )
    if complaint is None:
        return None

    try:
        previous_state = complaint.status
        next_state = validate_transition(previous_state, target_state, context)
        complaint.status = next_state.value
        session.add(
            ComplaintEvent(
                complaint_id=complaint.id,
                event_type="complaint_state_changed",
                actor_subject=context.actor_subject,
                previous_state=previous_state,
                resulting_state=next_state.value,
                reason=context.reason,
                correlation_id=correlation_id,
                visibility="citizen" if citizen_visible else "internal",
            )
        )
        session.commit()
        session.refresh(complaint)
    except Exception:
        session.rollback()
        raise
    return complaint
