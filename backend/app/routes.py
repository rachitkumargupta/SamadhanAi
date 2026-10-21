from fastapi import APIRouter, Depends, File, Form, HTTPException, Path, Query, Request, Response, UploadFile, status
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
