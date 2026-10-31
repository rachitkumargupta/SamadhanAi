from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from backend.app.agents.complaint_analyst import ComplaintAnalysis


ComplaintDescription = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=5000),
]
LocationText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=500),
]


class ComplaintCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: ComplaintDescription | None = None
    location_text: LocationText | None = None


class ComplaintRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_reference: str
    description: str | None
    location_text: str | None
    status: str
    created_at: datetime


class ComplaintListPage(BaseModel):
    items: list[ComplaintRead]
    limit: int
    offset: int
    next_offset: int | None


class ComplaintEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_type: str
    occurred_at: datetime


class ComplaintEventPage(BaseModel):
    items: list[ComplaintEventRead]
    limit: int
    offset: int
    next_offset: int | None


class ComplaintSubmissionRead(BaseModel):
    public_reference: str
    description: str | None
    location_text: str | None
    status: str
    analysis_status: str
    created_at: datetime


class ComplaintAnalysisStatusRead(BaseModel):
    public_reference: str
    status: str
    run_id: str | None = None
    result: ComplaintAnalysis | None = None
    human_review_required: bool
    message: str | None = None


class ComplaintAnalysisReviewItem(BaseModel):
    public_reference: str
    description: str | None
    location_text: str | None
    submitted_at: datetime
    analysis_status: str
    image_url: str
    result: ComplaintAnalysis | None = None


class ComplaintAnalysisReviewPage(BaseModel):
    items: list[ComplaintAnalysisReviewItem]
    limit: int
    offset: int
    next_offset: int | None


class ResolutionProofSubmissionRead(BaseModel):
    public_reference: str
    complaint_status: str
    work_status: str
    verification_status: str
    verification_deadline_at: datetime
    citizen_proof_url: str


class CitizenVerificationDecision(BaseModel):
    decision: Literal["confirm", "dispute"]
    reason: str | None = Field(default=None, max_length=2000)


VerificationReason = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]


class VerificationAuthorityDecision(BaseModel):
    outcome: Literal["confirm_completed", "return_for_work"]
    reason: VerificationReason


class VerificationDecisionRead(BaseModel):
    public_reference: str
    work_status: str
    verification_status: str
    action: str
    message: str


class VerificationReviewContextRead(BaseModel):
    public_reference: str
    complaint_status: str
    description: str | None
    location_text: str | None
    work_status: str
    verification_status: str
    verification_deadline_at: datetime | None
    assigned_officer_subject: str
    resolution_proof_url: str
    citizen_dispute_reason: str | None = None
    late_citizen_responses: list[dict] = Field(default_factory=list)


class NotificationRead(BaseModel):
    notification_id: str
    notification_type: str
    payload: dict
    created_at: datetime
    read_at: datetime | None = None


class NotificationPage(BaseModel):
    items: list[NotificationRead]
    limit: int
    offset: int
    next_offset: int | None
