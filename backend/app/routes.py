from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, status
from sqlalchemy.orm import Session

from backend.app.database import get_session
from backend.app.schemas import (
    ComplaintCreate,
    ComplaintEventPage,
    ComplaintEventRead,
    ComplaintListPage,
    ComplaintRead,
)
from backend.app.security import Actor, get_current_citizen
from backend.app.services import (
    get_owned_complaint,
    list_citizen_visible_events,
    list_owned_complaints,
    submit_complaint,
)


router = APIRouter(prefix="/api/v1/complaints", tags=["complaints"])


@router.post("", response_model=ComplaintRead, status_code=status.HTTP_201_CREATED)
def create_complaint(
    request: Request,
    payload: ComplaintCreate,
    session: Session = Depends(get_session),
    actor: Actor = Depends(get_current_citizen),
) -> ComplaintRead:
    complaint = submit_complaint(
        session,
        actor_subject=actor.subject,
        payload=payload,
        correlation_id=request.state.correlation_id,
    )
    return ComplaintRead.model_validate(complaint)


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
