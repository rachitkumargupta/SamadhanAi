import hashlib
import secrets
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from backend.app.domain.lifecycle import (
    ComplaintState,
    TransitionContext,
    validate_transition,
)
from backend.app.models import (
    BackgroundJob,
    Complaint,
    ComplaintAnalysis,
    ComplaintEvent,
    ComplaintMedia,
)
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


def submit_complaint_with_image(
    session: Session,
    *,
    actor_subject: str,
    description: str | None,
    location_text: str | None,
    correlation_id: str,
    object_key: str,
    normalized_image: bytes,
) -> tuple[Complaint, BackgroundJob]:
    """Atomically persist complaint, private-media reference, event, and job intent."""
    complaint = Complaint(
        public_reference=new_public_reference(),
        owner_subject=actor_subject,
        description=description,
        location_text=location_text,
        status=ComplaintState.SUBMITTED.value,
    )
    session.add(complaint)
    try:
        session.flush()
        media = ComplaintMedia(
            complaint_id=complaint.id,
            object_key=object_key,
            media_type="image/jpeg",
            purpose="complaint_image_normalized",
            size_bytes=len(normalized_image),
            sha256=hashlib.sha256(normalized_image).hexdigest(),
            uploaded_by=actor_subject,
        )
        session.add(media)
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
        job = BackgroundJob(
            complaint_id=complaint.id,
            media_id=media.id,
            work_type="complaint_analysis",
            idempotency_key=f"complaint_analysis:{complaint.id}",
            status="pending",
            max_attempts=3,
        )
        session.add(job)
        session.commit()
        session.refresh(complaint)
        session.refresh(job)
    except Exception:
        session.rollback()
        raise
    return complaint, job


def get_owned_complaint(
    session: Session, *, public_reference: str, actor_subject: str
) -> Complaint | None:
    statement = select(Complaint).where(
        Complaint.public_reference == public_reference,
        Complaint.owner_subject == actor_subject,
    )
    return session.scalar(statement)


def get_complaint_analysis(
    session: Session, *, complaint_id: UUID
) -> tuple[BackgroundJob | None, ComplaintAnalysis | None]:
    job = session.scalar(
        select(BackgroundJob)
        .where(
            BackgroundJob.complaint_id == complaint_id,
            BackgroundJob.work_type == "complaint_analysis",
        )
        .order_by(BackgroundJob.created_at.desc())
    )
    analysis = session.scalar(
        select(ComplaintAnalysis)
        .where(ComplaintAnalysis.complaint_id == complaint_id)
        .order_by(ComplaintAnalysis.created_at.desc())
    )
    return job, analysis


def media_object_is_referenced(session: Session, *, object_key: str) -> bool:
    return session.scalar(
        select(ComplaintMedia.id).where(ComplaintMedia.object_key == object_key)
    ) is not None


def list_analysis_review_items(
    session: Session, *, offset: int, limit: int
) -> tuple[list[tuple[Complaint, BackgroundJob, ComplaintAnalysis | None]], bool]:
    needs_human_review = ComplaintAnalysis.result["human_review_recommended"].as_boolean().is_(True)
    statement = (
        select(Complaint, BackgroundJob, ComplaintAnalysis)
        .join(BackgroundJob, BackgroundJob.complaint_id == Complaint.id)
        .outerjoin(ComplaintAnalysis, ComplaintAnalysis.complaint_id == Complaint.id)
        .where(
            BackgroundJob.work_type == "complaint_analysis",
            or_(BackgroundJob.status == "failed", needs_human_review),
        )
        .order_by(Complaint.created_at.asc(), Complaint.id.asc())
        .offset(offset)
        .limit(limit + 1)
    )
    rows = list(session.execute(statement).all())
    has_more = len(rows) > limit
    return rows[:limit], has_more


def get_complaint_media(session: Session, *, public_reference: str) -> ComplaintMedia | None:
    needs_human_review = ComplaintAnalysis.result["human_review_recommended"].as_boolean().is_(True)
    statement = (
        select(ComplaintMedia)
        .join(Complaint, Complaint.id == ComplaintMedia.complaint_id)
        .join(BackgroundJob, BackgroundJob.complaint_id == Complaint.id)
        .outerjoin(ComplaintAnalysis, ComplaintAnalysis.complaint_id == Complaint.id)
        .where(
            Complaint.public_reference == public_reference,
            ComplaintMedia.purpose == "complaint_image_normalized",
            BackgroundJob.work_type == "complaint_analysis",
            or_(BackgroundJob.status == "failed", needs_human_review),
        )
        .order_by(ComplaintMedia.created_at.desc())
    )
    return session.scalars(statement).first()


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
