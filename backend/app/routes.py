from datetime import datetime, timedelta, timezone
import hashlib
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
    ResolutionProofSubmissionRead,
    CitizenVerificationDecision,
    VerificationAuthorityDecision,
    VerificationDecisionRead,
    VerificationReviewContextRead,
    NotificationRead,
    NotificationPage,
)
from backend.app.agents.complaint_analyst import (
    MAX_IMAGE_BYTES,
    AnalystInputError,
    normalize_image,
)
from backend.app.security import (
    Actor,
    get_current_analyst_reviewer,
    get_current_citizen,
    get_current_resolution_officer,
    get_current_independent_verification_reviewer,
    get_current_senior_verification_authority,
    get_current_notification_recipient,
)
from backend.app.agents.monitoring_escalation import (
    AuthorityCandidate,
    EscalationEvent,
    EscalationAgentError,
    build_monitoring_escalation_agent,
)
from backend.app.models import (
    Complaint,
    ComplaintEvent,
    ComplaintMedia,
    MonitoringAuthority,
    MonitoringCase,
    MonitoringEvent,
    MonitoringJob,
    MonitoringNotification,
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
from backend.app.monitoring import MonitoringRegistrationError, record_resolution_submission


router = APIRouter(prefix="/api/v1/complaints", tags=["complaints"])
staff_router = APIRouter(prefix="/api/v1/staff/complaint-analysis", tags=["complaint-analysis-review"])
monitoring_router = APIRouter(prefix="/api/v1/staff/monitoring", tags=["monitoring"])
resolution_router = APIRouter(prefix="/api/v1/staff/complaints", tags=["resolution-proof"])
verification_review_router = APIRouter(prefix="/api/v1/staff/verification-reviews", tags=["verification-review"])
notifications_router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


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


@resolution_router.post(
    "/{public_reference}/resolution-proof",
    response_model=ResolutionProofSubmissionRead,
    status_code=status.HTTP_202_ACCEPTED,
)
def submit_resolution_proof(
    request: Request,
    image: UploadFile = File(...),
    public_reference: str = Path(max_length=32),
    session: Session = Depends(get_session),
    actor: Actor = Depends(get_current_resolution_officer),
) -> ResolutionProofSubmissionRead:
    """Assigned officer submits a private image; this never closes the complaint."""
    case = session.scalar(
        select(MonitoringCase)
        .join(Complaint, Complaint.id == MonitoringCase.complaint_id)
        .where(Complaint.public_reference == public_reference)
        .with_for_update()
    )
    if case is None:
        image.file.close()
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Assigned work item was not found."})
    if case.assigned_officer_subject != actor.subject:
        image.file.close()
        raise HTTPException(status_code=403, detail={"code": "assignment_required", "message": "Only the assigned officer can submit proof."})

    content_length = request.headers.get("content-length")
    if content_length and content_length.isdecimal() and int(content_length) > MAX_IMAGE_BYTES + 256_000:
        image.file.close()
        raise HTTPException(status_code=413, detail={"code": "request_too_large", "message": "Resolution proof upload exceeds the request limit."})
    raw_image = _read_upload_bounded(image)
    try:
        normalized_image, _ = normalize_image(raw_image)
    except AnalystInputError as exc:
        raise HTTPException(status_code=422, detail={"code": "invalid_image", "message": str(exc)}) from exc

    settings = get_settings()
    try:
        media_store = PrivateLocalMediaStore(settings.complaint_media_storage_dir)
        object_key = media_store.save_image(normalized_image)
    except OSError as exc:
        raise HTTPException(status_code=503, detail={"code": "media_storage_unavailable", "message": "Resolution proof could not be stored."}) from exc

    complaint = session.get(Complaint, case.complaint_id)
    if complaint is None:
        try:
            media_store.delete(object_key)
        except OSError:
            pass
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Complaint was not found."})

    now = datetime.now(timezone.utc)
    deadline = now + timedelta(hours=settings.citizen_verification_window_hours)
    previous_status = complaint.status
    try:
        session.add(ComplaintMedia(
            complaint_id=complaint.id,
            object_key=object_key,
            media_type="image/jpeg",
            purpose="resolution_proof_normalized",
            size_bytes=len(normalized_image),
            sha256=hashlib.sha256(normalized_image).hexdigest(),
            uploaded_by=actor.subject,
        ))
        session.flush()
        record_resolution_submission(
            session,
            complaint_id=complaint.id,
            actor_subject=actor.subject,
            evidence_ref=object_key,
            verification_deadline_at=deadline,
            submitted_at=now,
        )
        complaint.status = "resolved_pending_verification"
        session.add(ComplaintEvent(
            complaint_id=complaint.id,
            event_type="resolution_proof_submitted",
            actor_subject=actor.subject,
            previous_state=previous_status,
            resulting_state=complaint.status,
            correlation_id=getattr(request.state, "correlation_id", None),
            visibility="citizen",
            occurred_at=now,
        ))
        session.commit()
    except MonitoringRegistrationError as exc:
        session.rollback()
        try:
            media_store.delete(object_key)
        except OSError:
            pass
        raise HTTPException(status_code=409, detail={"code": "resolution_not_allowed", "message": str(exc)}) from exc
    except Exception:
        session.rollback()
        try:
            referenced = media_object_is_referenced(session, object_key=object_key)
        except Exception:
            referenced = True
        if not referenced:
            try:
                media_store.delete(object_key)
            except OSError:
                pass
        raise

    return ResolutionProofSubmissionRead(
        public_reference=complaint.public_reference,
        complaint_status=complaint.status,
        work_status="resolution_submitted",
        verification_status="not_started",
        verification_deadline_at=deadline,
        citizen_proof_url=f"/api/v1/complaints/{complaint.public_reference}/verification-proof",
    )


def _read_resolution_proof(session: Session, case: MonitoringCase) -> Response:
    if not case.resolution_evidence_ref:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Resolution proof was not found."})
    media = session.scalar(select(ComplaintMedia).where(
        ComplaintMedia.complaint_id == case.complaint_id,
        ComplaintMedia.object_key == case.resolution_evidence_ref,
        ComplaintMedia.purpose == "resolution_proof_normalized",
    ))
    if media is None:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Resolution proof was not found."})
    try:
        content = PrivateLocalMediaStore(get_settings().complaint_media_storage_dir).read_image(media.object_key)
        if len(content) != media.size_bytes or hashlib.sha256(content).hexdigest() != media.sha256:
            raise ValueError("Stored resolution proof integrity check failed.")
    except (OSError, ValueError):
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Resolution proof was not found."}) from None
    return Response(content=content, media_type="image/jpeg", headers={
        "Cache-Control": "private, no-store",
        "X-Content-Type-Options": "nosniff",
    })


@router.get("/{public_reference}/verification-proof")
def read_citizen_resolution_proof(
    public_reference: str = Path(max_length=32),
    session: Session = Depends(get_session),
    actor: Actor = Depends(get_current_citizen),
) -> Response:
    complaint = get_owned_complaint(session, public_reference=public_reference, actor_subject=actor.subject)
    if complaint is None:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Complaint was not found."})
    case = session.scalar(select(MonitoringCase).where(MonitoringCase.complaint_id == complaint.id))
    if case is None or case.verification_status not in {"not_started", "pending_citizen", "review_required", "disputed", "approved"}:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Resolution proof was not found."})
    return _read_resolution_proof(session, case)


def _locked_complaint_case(session: Session, public_reference: str):
    row = session.execute(
        select(MonitoringCase, Complaint)
        .join(Complaint, Complaint.id == MonitoringCase.complaint_id)
        .where(Complaint.public_reference == public_reference)
        .with_for_update()
    ).first()
    return row if row is not None else (None, None)


def _add_verification_event(session: Session, case: MonitoringCase, event_type: str, data: dict, now: datetime) -> MonitoringEvent:
    event = MonitoringEvent(
        monitoring_case_id=case.id,
        event_type=event_type,
        idempotency_key=f"verification-action:{case.id}:{uuid4()}",
        data=data,
        occurred_at=now,
    )
    session.add(event)
    session.flush()
    return event


def _add_verification_notification(
    session: Session,
    case: MonitoringCase,
    *,
    recipient: str,
    notification_type: str,
    payload: dict,
    event: MonitoringEvent,
    now: datetime,
) -> None:
    session.add(MonitoringNotification(
        monitoring_case_id=case.id,
        recipient_subject=recipient,
        notification_type=notification_type,
        idempotency_key=f"verification-action:{event.id}:{hashlib.sha256(recipient.encode()).hexdigest()[:16]}:{notification_type}",
        payload=payload,
        created_at=now,
    ))


def _available_senior_authority(session: Session, case: MonitoringCase) -> MonitoringAuthority | None:
    if case.senior_authority_subject:
        assigned = session.scalar(select(MonitoringAuthority).where(
            MonitoringAuthority.subject == case.senior_authority_subject,
            MonitoringAuthority.active.is_(True),
            MonitoringAuthority.authority_type == "senior_authority",
            MonitoringAuthority.jurisdiction_id == case.jurisdiction_id,
            MonitoringAuthority.department_id == case.department_id,
        ))
        if assigned is not None:
            return assigned
    return session.scalar(
        select(MonitoringAuthority)
        .where(
            MonitoringAuthority.active.is_(True),
            MonitoringAuthority.authority_type == "senior_authority",
            MonitoringAuthority.jurisdiction_id == case.jurisdiction_id,
            MonitoringAuthority.department_id == case.department_id,
            MonitoringAuthority.escalation_level > case.current_escalation_level,
        )
        .order_by(MonitoringAuthority.escalation_level, MonitoringAuthority.id)
        .limit(1)
    )


@router.post("/{public_reference}/verification-decision", response_model=VerificationDecisionRead)
def submit_citizen_verification_decision(
    request: Request,
    decision: CitizenVerificationDecision,
    public_reference: str = Path(max_length=32),
    session: Session = Depends(get_session),
    actor: Actor = Depends(get_current_citizen),
) -> VerificationDecisionRead:
    case, complaint = _locked_complaint_case(session, public_reference)
    if case is None or complaint.owner_subject != actor.subject:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Complaint was not found."})
    if case.verification_deadline_at is None or case.resolution_evidence_ref is None:
        raise HTTPException(status_code=409, detail={"code": "verification_not_ready", "message": "Resolution proof is not awaiting a citizen decision."})
    if case.verification_status not in {"not_started", "pending_citizen", "review_required"}:
        raise HTTPException(status_code=409, detail={"code": "verification_not_pending", "message": "This case is no longer awaiting a citizen decision."})

    if decision.decision == "dispute" and not (decision.reason and decision.reason.strip()):
        raise HTTPException(status_code=422, detail={"code": "dispute_reason_required", "message": "Add a short reason for disputing the resolution."})

    now = datetime.now(timezone.utc)
    is_review_active = case.verification_status == "review_required"
    window_open = now <= case.verification_deadline_at
    if is_review_active or not window_open:
        event = _add_verification_event(session, case, "CITIZEN_LATE_VERIFICATION_RESPONSE", {
            "decision": decision.decision,
            "reason": decision.reason,
            "received_at": now.isoformat(),
            "reviewer_subject": case.independent_reviewer_subject,
        }, now)
        if case.independent_reviewer_subject:
            _add_verification_notification(session, case, recipient=case.independent_reviewer_subject,
                notification_type="late_citizen_response_for_review",
                payload={"complaint_reference": public_reference, "decision": decision.decision, "reason": decision.reason},
                event=event, now=now)
        session.add(ComplaintEvent(
            complaint_id=complaint.id,
            event_type="citizen_late_verification_response_recorded",
            actor_subject=actor.subject,
            previous_state=complaint.status,
            resulting_state=complaint.status,
            correlation_id=getattr(request.state, "correlation_id", None),
            visibility="citizen",
            occurred_at=now,
        ))
        session.commit()
        return VerificationDecisionRead(
            public_reference=public_reference,
            work_status=case.work_status,
            verification_status=case.verification_status,
            action="recorded_for_independent_reviewer" if case.independent_reviewer_subject else "recorded_after_deadline",
            message=(
                "Your response was recorded for the assigned independent reviewer. It does not automatically close or cancel the review."
                if case.independent_reviewer_subject
                else "Your response was recorded after the deadline. The monitoring worker will route the case for independent review; this response does not close it."
            ),
        )

    if case.verification_status not in {"not_started", "pending_citizen"} or case.work_status not in {"resolution_submitted", "pending_citizen_verification"}:
        raise HTTPException(status_code=409, detail={"code": "verification_not_pending", "message": "This case is not awaiting a citizen decision."})
    previous_status = complaint.status
    if decision.decision == "confirm":
        case.verification_status = "approved"
        case.work_status = "closed"
        complaint.status = "closed"
        event = _add_verification_event(session, case, "CITIZEN_VERIFICATION_CONFIRMED", {
            "decision": "confirm",
            "decided_by": actor.subject,
            "decided_at": now.isoformat(),
        }, now)
        action = "closed"
        message = "Your confirmation was recorded and the complaint is closed."
        citizen_event = "citizen_confirmed_resolution"
    else:
        authority = _available_senior_authority(session, case)
        if authority is None:
            raise HTTPException(status_code=503, detail={"code": "senior_authority_unavailable", "message": "No eligible senior authority is configured for this department and jurisdiction."})
        case.verification_status = "disputed"
        case.work_status = "disputed"
        case.senior_authority_subject = authority.subject
        complaint.status = "verification_disputed"
        event = _add_verification_event(session, case, "CITIZEN_VERIFICATION_DISPUTED", {
            "decision": "dispute",
            "reason": decision.reason.strip(),
            "decided_by": actor.subject,
            "senior_authority_subject": authority.subject,
            "decided_at": now.isoformat(),
        }, now)
        _add_verification_notification(session, case, recipient=authority.subject,
            notification_type="citizen_disputed_resolution",
            payload={"complaint_reference": public_reference, "reason": decision.reason.strip()},
            event=event, now=now)
        action = "sent_to_senior_authority"
        message = "Your dispute was sent to the assigned senior authority. The complaint remains open."
        citizen_event = "citizen_disputed_resolution"

    session.add(ComplaintEvent(
        complaint_id=complaint.id,
        event_type=citizen_event,
        actor_subject=actor.subject,
        previous_state=previous_status,
        resulting_state=complaint.status,
        correlation_id=getattr(request.state, "correlation_id", None),
        visibility="citizen",
        occurred_at=now,
    ))
    if decision.decision == "confirm":
        _add_verification_notification(session, case, recipient=complaint.owner_subject,
            notification_type="complaint_closed_after_citizen_confirmation",
            payload={"complaint_reference": public_reference, "status": "closed"}, event=event, now=now)
    session.commit()
    return VerificationDecisionRead(
        public_reference=public_reference,
        work_status=case.work_status,
        verification_status=case.verification_status,
        action=action,
        message=message,
    )


def _apply_authority_verification_decision(
    request: Request,
    public_reference: str,
    decision: VerificationAuthorityDecision,
    session: Session,
    actor: Actor,
    *,
    independent_reviewer: bool,
) -> VerificationDecisionRead:
    case, complaint = _locked_complaint_case(session, public_reference)
    if case is None:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Verification case was not found."})
    if independent_reviewer:
        if case.independent_reviewer_subject != actor.subject or case.verification_status != "review_required":
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Assigned verification review was not found."})
        event_type = "INDEPENDENT_REVIEWER_VERIFICATION_DECIDED"
        actor_label = "independent_reviewer"
    else:
        if case.senior_authority_subject != actor.subject or case.verification_status != "disputed":
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Assigned senior-authority dispute was not found."})
        event_type = "SENIOR_AUTHORITY_VERIFICATION_DECIDED"
        actor_label = "senior_authority"

    now = datetime.now(timezone.utc)
    previous_status = complaint.status
    event = _add_verification_event(session, case, event_type, {
        "outcome": decision.outcome,
        "reason": decision.reason.strip(),
        "decided_by": actor.subject,
        "decision_role": actor_label,
        "resolution_evidence_ref": case.resolution_evidence_ref,
        "decided_at": now.isoformat(),
    }, now)

    if decision.outcome == "confirm_completed":
        case.verification_status = "approved"
        case.work_status = "closed"
        complaint.status = "closed"
        action = "closed"
        citizen_event = "verification_review_confirmed_completion"
        message = "The work was confirmed as complete and the complaint is closed."
        notification_type = "verification_review_closed_complaint"
    else:
        case.work_status = "in_progress"
        case.verification_status = "not_started"
        case.verification_deadline_at = None
        case.resolution_evidence_ref = None
        case.verification_routed_at = None
        case.independent_reviewer_subject = None
        case.work_completed_at = None
        complaint.status = "in_progress"
        action = "returned_to_officer"
        citizen_event = "verification_review_returned_work_for_rework"
        message = "The work was returned to the assigned officer for further action. The complaint remains open."
        notification_type = "verification_work_returned_to_officer"

    session.add(ComplaintEvent(
        complaint_id=complaint.id,
        event_type=citizen_event,
        actor_subject=actor.subject,
        previous_state=previous_status,
        resulting_state=complaint.status,
        correlation_id=getattr(request.state, "correlation_id", None),
        visibility="citizen",
        occurred_at=now,
    ))
    _add_verification_notification(session, case, recipient=complaint.owner_subject,
        notification_type="verification_decision_recorded",
        payload={"complaint_reference": public_reference, "outcome": decision.outcome, "status": complaint.status},
        event=event, now=now)
    if decision.outcome == "return_for_work":
        _add_verification_notification(session, case, recipient=case.assigned_officer_subject,
            notification_type=notification_type,
            payload={"complaint_reference": public_reference, "reason": decision.reason.strip()},
            event=event, now=now)
        if independent_reviewer and case.senior_authority_subject:
            _add_verification_notification(session, case, recipient=case.senior_authority_subject,
                notification_type="independent_review_found_work_incomplete",
                payload={"complaint_reference": public_reference, "reason": decision.reason.strip()},
                event=event, now=now)
    session.commit()
    return VerificationDecisionRead(
        public_reference=public_reference,
        work_status=case.work_status,
        verification_status=case.verification_status,
        action=action,
        message=message,
    )


def _late_citizen_responses(session: Session, case: MonitoringCase) -> list[dict]:
    events = session.scalars(
        select(MonitoringEvent)
        .where(
            MonitoringEvent.monitoring_case_id == case.id,
            MonitoringEvent.event_type == "CITIZEN_LATE_VERIFICATION_RESPONSE",
        )
        .order_by(MonitoringEvent.occurred_at, MonitoringEvent.id)
    )
    return [event.data for event in events]


def _citizen_dispute_reason(session: Session, case: MonitoringCase) -> str | None:
    event = session.scalar(
        select(MonitoringEvent)
        .where(
            MonitoringEvent.monitoring_case_id == case.id,
            MonitoringEvent.event_type == "CITIZEN_VERIFICATION_DISPUTED",
        )
        .order_by(MonitoringEvent.occurred_at.desc(), MonitoringEvent.id.desc())
        .limit(1)
    )
    return event.data.get("reason") if event is not None else None


def _verification_context(session: Session, complaint: Complaint, case: MonitoringCase) -> VerificationReviewContextRead:
    proof_path = (
        f"/api/v1/staff/complaints/{case.complaint_reference}/verification-proof"
        if case.verification_status == "disputed"
        else f"/api/v1/staff/verification-reviews/{case.complaint_reference}/proof"
    )
    return VerificationReviewContextRead(
        public_reference=case.complaint_reference,
        complaint_status=complaint.status,
        description=complaint.description,
        location_text=complaint.location_text,
        work_status=case.work_status,
        verification_status=case.verification_status,
        verification_deadline_at=case.verification_deadline_at,
        assigned_officer_subject=case.assigned_officer_subject,
        resolution_proof_url=proof_path,
        citizen_dispute_reason=_citizen_dispute_reason(session, case),
        late_citizen_responses=_late_citizen_responses(session, case),
    )


@resolution_router.get("/{public_reference}/verification-review", response_model=VerificationReviewContextRead)
def read_senior_authority_verification_case(
    public_reference: str = Path(max_length=32),
    session: Session = Depends(get_session),
    actor: Actor = Depends(get_current_senior_verification_authority),
) -> VerificationReviewContextRead:
    case, complaint = _locked_complaint_case(session, public_reference)
    if case is None or case.senior_authority_subject != actor.subject or case.verification_status != "disputed":
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Assigned senior-authority dispute was not found."})
    return _verification_context(session, complaint, case)


@verification_review_router.get("/{public_reference}", response_model=VerificationReviewContextRead)
def read_independent_reviewer_case(
    public_reference: str = Path(max_length=32),
    session: Session = Depends(get_session),
    actor: Actor = Depends(get_current_independent_verification_reviewer),
) -> VerificationReviewContextRead:
    case, complaint = _locked_complaint_case(session, public_reference)
    if case is None or case.independent_reviewer_subject != actor.subject or case.verification_status != "review_required":
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Assigned verification review was not found."})
    return _verification_context(session, complaint, case)


@resolution_router.get("/{public_reference}/verification-proof")
def read_senior_authority_proof(
    public_reference: str = Path(max_length=32),
    session: Session = Depends(get_session),
    actor: Actor = Depends(get_current_senior_verification_authority),
) -> Response:
    case = session.scalar(
        select(MonitoringCase)
        .join(Complaint, Complaint.id == MonitoringCase.complaint_id)
        .where(Complaint.public_reference == public_reference)
    )
    if case is None or case.senior_authority_subject != actor.subject or case.verification_status != "disputed":
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Assigned disputed proof was not found."})
    return _read_resolution_proof(session, case)


@resolution_router.post("/{public_reference}/verification-decision", response_model=VerificationDecisionRead)
def decide_disputed_verification(
    request: Request,
    decision: VerificationAuthorityDecision,
    public_reference: str = Path(max_length=32),
    session: Session = Depends(get_session),
    actor: Actor = Depends(get_current_senior_verification_authority),
) -> VerificationDecisionRead:
    """Assigned senior authority confirms proof or returns the work for rework."""
    return _apply_authority_verification_decision(request, public_reference, decision, session, actor, independent_reviewer=False)


@verification_review_router.post("/{public_reference}/decision", response_model=VerificationDecisionRead)
def decide_overdue_verification(
    request: Request,
    decision: VerificationAuthorityDecision,
    public_reference: str = Path(max_length=32),
    session: Session = Depends(get_session),
    actor: Actor = Depends(get_current_independent_verification_reviewer),
) -> VerificationDecisionRead:
    """Assigned independent reviewer decides whether proof demonstrates completion."""
    return _apply_authority_verification_decision(request, public_reference, decision, session, actor, independent_reviewer=True)


@verification_review_router.get("/{public_reference}/proof")
def read_independent_reviewer_proof(
    public_reference: str = Path(max_length=32),
    session: Session = Depends(get_session),
    actor: Actor = Depends(get_current_independent_verification_reviewer),
) -> Response:
    case = session.scalar(
        select(MonitoringCase)
        .join(Complaint, Complaint.id == MonitoringCase.complaint_id)
        .where(Complaint.public_reference == public_reference)
    )
    if case is None or case.independent_reviewer_subject != actor.subject or case.verification_status != "review_required":
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Assigned verification proof was not found."})
    return _read_resolution_proof(session, case)


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


@notifications_router.get("", response_model=NotificationPage)
def read_notification_inbox(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=10_000),
    unread_only: bool = Query(default=False),
    session: Session = Depends(get_session),
    actor: Actor = Depends(get_current_notification_recipient),
) -> NotificationPage:
    """Return only notification rows addressed to the authenticated subject."""
    statement = select(MonitoringNotification).where(
        MonitoringNotification.recipient_subject == actor.subject
    )
    if unread_only:
        statement = statement.where(MonitoringNotification.read_at.is_(None))
    rows = list(session.scalars(
        statement.order_by(
            MonitoringNotification.created_at.desc(),
            MonitoringNotification.id.desc(),
        ).offset(offset).limit(limit + 1)
    ))
    has_more = len(rows) > limit
    rows = rows[:limit]
    return NotificationPage(
        items=[NotificationRead(
            notification_id=str(row.id),
            notification_type=row.notification_type,
            payload=row.payload,
            created_at=row.created_at,
            read_at=row.read_at,
        ) for row in rows],
        limit=limit,
        offset=offset,
        next_offset=offset + limit if has_more else None,
    )


@notifications_router.patch("/{notification_id}/read", response_model=NotificationRead)
def mark_notification_read(
    notification_id: UUID,
    session: Session = Depends(get_session),
    actor: Actor = Depends(get_current_notification_recipient),
) -> NotificationRead:
    """Mark only the authenticated recipient's notification as read; repeat calls are safe."""
    row = session.scalar(
        select(MonitoringNotification)
        .where(
            MonitoringNotification.id == notification_id,
            MonitoringNotification.recipient_subject == actor.subject,
        )
        .with_for_update()
    )
    if row is None:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Notification was not found."})
    if row.read_at is None:
        row.read_at = datetime.now(timezone.utc)
        session.commit()
        session.refresh(row)
    return NotificationRead(
        notification_id=str(row.id),
        notification_type=row.notification_type,
        payload=row.payload,
        created_at=row.created_at,
        read_at=row.read_at,
    )


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
