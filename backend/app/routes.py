from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Path, Query, Request, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database import get_session
from backend.app.schemas import (
    ComplaintAnalysisStatusRead,
    ComplaintAnalysisReviewItem,
    ComplaintAnalysisReviewPage,
    ComplaintEventPage,
    ComplaintEventRead,
    ComplaintListPage,
    ComplaintRead,
    ComplaintSubmissionRead,
)
from backend.app.agents.complaint_analyst import (
    MAX_IMAGE_BYTES,
    AnalystInputError,
    normalize_image,
)
from backend.app.security import Actor, get_current_analyst_reviewer, get_current_citizen
from backend.app.agents.monitoring_escalation import (
    AuthorityCandidate,
    EscalationEvent,
    EscalationAgentError,
    build_monitoring_escalation_agent,
)
from backend.app.models import (
    Complaint,
    ComplaintAnalysis,
    MonitoringAuthority,
    MonitoringCase,
    MonitoringEvent,
    MonitoringJob,
)
from backend.app.storage import PrivateLocalMediaStore
from backend.app.services import (
    get_complaint_analysis,
    get_complaint_media,
    get_owned_complaint,
    list_citizen_visible_events,
    list_analysis_review_items,
    list_owned_complaints,
    media_object_is_referenced,
    submit_complaint_with_image,
)
from backend.app.config import get_settings


router = APIRouter(prefix="/api/v1/complaints", tags=["complaints"])
staff_router = APIRouter(prefix="/api/v1/staff/complaint-analysis", tags=["complaint-analysis-review"])
monitoring_router = APIRouter(prefix="/api/v1/staff/monitoring", tags=["monitoring"])


@staff_router.get("/complaints/{complaint_id}/routing-proposal")
def read_agent2_routing_proposal(
    complaint_id: UUID,
    session: Session = Depends(get_session),
    actor: Actor = Depends(get_current_analyst_reviewer),
) -> dict[str, Any]:
    """Return the separately saved Agent 2 proposal to authorized staff."""
    complaint = session.get(Complaint, complaint_id)
    if complaint is None:
        raise HTTPException(status_code=404, detail="Complaint was not found.")

    analysis = session.scalar(
        select(ComplaintAnalysis)
        .where(ComplaintAnalysis.complaint_id == complaint_id)
        .order_by(ComplaintAnalysis.created_at.desc())
        .limit(1)
    )
    if analysis is None or analysis.routing_proposal is None:
        raise HTTPException(status_code=404, detail="Agent 2 routing proposal was not found.")
    return {
        "complaint_id": str(complaint.id),
        "routing_proposal": analysis.routing_proposal,
    }


@monitoring_router.post("/escalation-jobs/{job_id}")
def process_monitoring_escalation_job(
    job_id: UUID,
    event_input: EscalationEvent,
    session: Session = Depends(get_session),
    actor: Actor = Depends(get_current_analyst_reviewer),
):
    """Process one existing confirmed breach job and persist its Agent 3 proposal."""
    job = session.scalar(
        select(MonitoringJob).where(MonitoringJob.id == job_id).with_for_update()
    )
    if job is None or job.job_type != "agent3_sla_escalation":
        raise HTTPException(status_code=404, detail="Escalation job was not found.")

    stored_event = session.get(MonitoringEvent, job.event_id)
    case = session.get(MonitoringCase, job.monitoring_case_id)
    if (
        stored_event is None
        or case is None
        or stored_event.monitoring_case_id != job.monitoring_case_id
        or stored_event.event_type != "SLA_BREACHED"
        or case.sla_status != "breached"
        or event_input.event_type != "SLA_BREACHED"
        or not event_input.breach_confirmed
        or event_input.event_id != str(stored_event.id)
    ):
        raise HTTPException(status_code=422, detail="A matching confirmed SLA breach is required.")

    if job.status == "succeeded" and job.result is not None:
        return {"record_id": str(job.id), "agent3_output": job.result}
    if job.status != "pending":
        raise HTTPException(status_code=409, detail="Escalation job is not pending.")
    if job.attempt_count >= job.max_attempts:
        raise HTTPException(status_code=409, detail="Escalation job has exhausted its attempts.")

    requested_ids = set()
    try:
        requested_ids = {UUID(item.authority_id) for item in event_input.escalation_hierarchy}
    except ValueError:
        raise HTTPException(status_code=422, detail="Authority IDs must be valid UUIDs.") from None

    authorities = list(session.scalars(
        select(MonitoringAuthority).where(
            MonitoringAuthority.id.in_(requested_ids),
            MonitoringAuthority.active.is_(True),
            MonitoringAuthority.authority_type == "senior_authority",
            MonitoringAuthority.jurisdiction_id == case.jurisdiction_id,
            MonitoringAuthority.escalation_level > case.current_escalation_level,
        )
    )) if requested_ids else []
    authorities = [
        authority for authority in authorities
        if authority.department_id in (case.department_id, None)
    ]
    if len(authorities) != len(requested_ids):
        raise HTTPException(status_code=422, detail="All escalation authorities must be currently eligible.")

    trusted_input = event_input.model_copy(update={
        "event_id": str(stored_event.id),
        "event_type": "SLA_BREACHED",
        "breach_confirmed": True,
        "complaint_reference": case.complaint_reference,
        "ticket_reference": case.complaint_reference,
        "ticket_state": case.work_status,
        "sla_policy_id": case.sla_policy_id,
        "sla_policy_version": case.sla_policy_version,
        "deadline_utc": case.sla_deadline_at.isoformat(),
        "breached_at_utc": (case.sla_breached_at or stored_event.occurred_at).isoformat(),
        "escalation_hierarchy": [AuthorityCandidate(
            authority_id=str(item.id),
            display_name=item.display_name,
            level=f"level_{item.escalation_level}",
            eligibility_basis=item.eligibility_basis,
        ) for item in authorities],
    })

    # Claim the job before calling the provider so the background worker will
    # not claim this same pending item concurrently.
    now = datetime.now(timezone.utc)
    claim_owner = f"api-escalation:{actor.subject}:{uuid4()}"[:120]
    job.status = "running"
    job.attempt_count += 1
    job.lease_owner = claim_owner
    job.lease_expires_at = now + timedelta(seconds=180)
    session.commit()

    try:
        proposal = build_monitoring_escalation_agent(get_settings()).handle(trusted_input)
    except EscalationAgentError as exc:
        session.refresh(job)
        if job.status != "running" or job.lease_owner != claim_owner:
            raise HTTPException(status_code=409, detail="Escalation job claim was lost.") from exc
        job.status = "failed" if job.attempt_count >= job.max_attempts else "pending"
        job.error_code = f"agent3_failed_{type(exc).__name__}"
        job.lease_owner = None
        job.lease_expires_at = None
        if job.status == "failed":
            job.completed_at = datetime.now(timezone.utc)
        session.commit()
        raise HTTPException(status_code=503, detail="Agent 3 could not process the escalation job.") from exc

    session.refresh(job)
    if job.status != "running" or job.lease_owner != claim_owner:
        raise HTTPException(status_code=409, detail="Escalation job claim was lost.")
    job.result = proposal.model_dump(mode="json")
    job.status = "succeeded"
    job.lease_owner = None
    job.lease_expires_at = None
    job.error_code = None
    job.completed_at = datetime.now(timezone.utc)
    session.add(MonitoringEvent(
        monitoring_case_id=case.id,
        event_type="AGENT3_ESCALATION_PROPOSAL_RECORDED",
        idempotency_key=f"agent3-proposal:{job.id}",
        data=proposal.model_dump(mode="json"),
    ))
    session.commit()
    session.refresh(job)
    return {"record_id": str(job.id), "agent3_output": proposal.model_dump(mode="json")}


@monitoring_router.get("/escalation-jobs/{job_id}")
def read_monitoring_escalation_job(
    job_id: UUID,
    session: Session = Depends(get_session),
    actor: Actor = Depends(get_current_analyst_reviewer),
):
    """Return the status and saved proposal for one Agent 3 escalation job."""
    job = session.get(MonitoringJob, job_id)
    if job is None or job.job_type != "agent3_sla_escalation":
        raise HTTPException(status_code=404, detail="Escalation job was not found.")

    proposal_events = list(session.scalars(
        select(MonitoringEvent)
        .where(
            MonitoringEvent.monitoring_case_id == job.monitoring_case_id,
            MonitoringEvent.event_type == "AGENT3_ESCALATION_PROPOSAL_RECORDED",
            MonitoringEvent.idempotency_key == f"agent3-proposal:{job.id}",
        )
        .order_by(MonitoringEvent.occurred_at, MonitoringEvent.id)
    ))
    return {
        "job_id": str(job.id),
        "status": job.status,
        "proposal": job.result,
        "proposal_events": [
            {
                "event_id": str(event.id),
                "event_type": event.event_type,
                "occurred_at": event.occurred_at.isoformat(),
                "proposal": event.data,
            }
            for event in proposal_events
        ],
    }


@staff_router.get("/reviews", response_model=ComplaintAnalysisReviewPage)
def read_analysis_review_queue(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=10_000),
    session: Session = Depends(get_session),
    actor: Actor = Depends(get_current_analyst_reviewer),
) -> ComplaintAnalysisReviewPage:
    rows, has_more = list_analysis_review_items(session, offset=offset, limit=limit)
    return ComplaintAnalysisReviewPage(
        items=[
            ComplaintAnalysisReviewItem(
                public_reference=complaint.public_reference,
                description=complaint.description,
                location_text=complaint.location_text,
                submitted_at=complaint.created_at,
                analysis_status=job.status,
                image_url=f"/api/v1/staff/complaint-analysis/reviews/{complaint.public_reference}/image",
                result=analysis.result if analysis is not None else None,
            )
            for complaint, job, analysis in rows
        ],
        limit=limit,
        offset=offset,
        next_offset=offset + limit if has_more else None,
    )


@staff_router.get("/reviews/{public_reference}/image")
def read_analysis_review_image(
    public_reference: str = Path(max_length=32),
    session: Session = Depends(get_session),
    actor: Actor = Depends(get_current_analyst_reviewer),
) -> Response:
    media = get_complaint_media(session, public_reference=public_reference)
    if media is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Review evidence was not found."},
        )
    try:
        image_bytes = PrivateLocalMediaStore(get_settings().complaint_media_storage_dir).read_image(
            media.object_key
        )
    except (OSError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Review evidence was not found."},
        ) from None
    return Response(
        content=image_bytes,
        media_type="image/jpeg",
        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"},
    )


def _read_upload_bounded(upload: UploadFile) -> bytes:
    content = bytearray()
    try:
        while chunk := upload.file.read(64 * 1024):
            content.extend(chunk)
            if len(content) > MAX_IMAGE_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail={"code": "image_too_large", "message": "Image exceeds the 10 MiB limit."},
                )
        if not content:
            raise HTTPException(
                status_code=422,
                detail={"code": "invalid_image", "message": "A non-empty image is required."},
            )
        return bytes(content)
    finally:
        upload.file.close()


@router.post("", response_model=ComplaintSubmissionRead, status_code=status.HTTP_201_CREATED)
def create_complaint(
    request: Request,
    image: UploadFile = File(...),
    description: str | None = Form(default=None, max_length=5000),
    location_text: str | None = Form(default=None, max_length=500),
    session: Session = Depends(get_session),
    actor: Actor = Depends(get_current_citizen),
) -> ComplaintSubmissionRead:
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdecimal() and int(content_length) > MAX_IMAGE_BYTES + 256_000:
        image.file.close()
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={"code": "request_too_large", "message": "Complaint upload exceeds the request limit."},
        )
    raw_image = _read_upload_bounded(image)
    try:
        normalized_image, _ = normalize_image(raw_image)
    except AnalystInputError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "invalid_image", "message": str(exc)},
        ) from exc
    settings = get_settings()
    try:
        media_store = PrivateLocalMediaStore(settings.complaint_media_storage_dir)
        object_key = media_store.save_image(normalized_image)
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "media_storage_unavailable", "message": "The complaint could not be stored."},
        ) from exc
    try:
        complaint, _ = submit_complaint_with_image(
            session,
            actor_subject=actor.subject,
            description=description.strip() if description and description.strip() else None,
            location_text=(location_text.strip() if location_text and location_text.strip() else None),
            correlation_id=request.state.correlation_id,
            object_key=object_key,
            normalized_image=normalized_image,
        )
    except Exception:
        session.rollback()
        try:
            committed_reference = media_object_is_referenced(session, object_key=object_key)
        except Exception:
            # A database outage leaves the commit outcome unknown; keep media rather than
            # risk deleting an image referenced by a successfully committed complaint.
            committed_reference = True
        if not committed_reference:
            try:
                media_store.delete(object_key)
            except OSError:
                pass
        raise
    return ComplaintSubmissionRead(
        public_reference=complaint.public_reference,
        description=complaint.description,
        location_text=complaint.location_text,
        status=complaint.status,
        analysis_status="pending",
        created_at=complaint.created_at,
    )


@router.get("", response_model=ComplaintListPage)
def read_complaints(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=10_000),
    session: Session = Depends(get_session),
    actor: Actor = Depends(get_current_citizen),
) -> ComplaintListPage:
    complaints, has_more = list_owned_complaints(
        session,
        actor_subject=actor.subject,
        offset=offset,
        limit=limit,
    )
    return ComplaintListPage(
        items=[ComplaintRead.model_validate(item) for item in complaints],
        limit=limit,
        offset=offset,
        next_offset=offset + limit if has_more else None,
    )


@router.get("/{public_reference}", response_model=ComplaintRead)
def read_complaint(
    public_reference: str = Path(max_length=32),
    session: Session = Depends(get_session),
    actor: Actor = Depends(get_current_citizen),
) -> ComplaintRead:
    complaint = get_owned_complaint(
        session,
        public_reference=public_reference,
        actor_subject=actor.subject,
    )
    if complaint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Complaint was not found."},
        )
    return ComplaintRead.model_validate(complaint)


@router.get("/{public_reference}/analysis", response_model=ComplaintAnalysisStatusRead)
def read_complaint_analysis(
    public_reference: str = Path(max_length=32),
    session: Session = Depends(get_session),
    actor: Actor = Depends(get_current_citizen),
) -> ComplaintAnalysisStatusRead:
    complaint = get_owned_complaint(
        session,
        public_reference=public_reference,
        actor_subject=actor.subject,
    )
    if complaint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Complaint was not found."},
        )
    job, analysis = get_complaint_analysis(session, complaint_id=complaint.id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "analysis_not_found", "message": "Analysis was not found."},
        )
    result = analysis.result if analysis is not None else None
    is_failed = job.status == "failed"
    return ComplaintAnalysisStatusRead(
        public_reference=complaint.public_reference,
        status=job.status,
        run_id=str(analysis.agent_run_id) if analysis is not None else None,
        result=result,
        human_review_required=is_failed or bool(result and result.get("human_review_recommended")),
        message=(
            "Analysis could not be completed. The complaint remains available for manual review."
            if is_failed
            else None
        ),
    )


@router.get("/{public_reference}/events", response_model=ComplaintEventPage)
def read_complaint_events(
    public_reference: str = Path(max_length=32),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=10_000),
    session: Session = Depends(get_session),
    actor: Actor = Depends(get_current_citizen),
) -> ComplaintEventPage:
    complaint = get_owned_complaint(
        session,
        public_reference=public_reference,
        actor_subject=actor.subject,
    )
    if complaint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Complaint was not found."},
        )
    events, has_more = list_citizen_visible_events(
        session,
        complaint_id=complaint.id,
        offset=offset,
        limit=limit,
    )
    return ComplaintEventPage(
        items=[ComplaintEventRead.model_validate(event) for event in events],
        limit=limit,
        offset=offset,
        next_offset=offset + limit if has_more else None,
    )
