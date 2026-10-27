
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# 1. Categories that Agent 1 can identify
class Category(str, Enum):
    DRAINAGE_SEWAGE = "drainage_sewage"
    STREETLIGHTS_ELECTRICAL = "streetlights_electrical"
    ROAD_DAMAGE = "road_damage"
    WASTE_MANAGEMENT = "waste_management"
    WATER_SUPPLY = "water_supply"
    UNKNOWN = "unknown"


# 2. Severity levels
class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


# 3. A single problem detected by Agent 1
class DetectedProblem(BaseModel):
    model_config = ConfigDict(extra="allow")

    problem_id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    category: Category = Category.UNKNOWN
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)
    location: str | None = None
    severity_hint: Severity = Severity.UNKNOWN
    requires_human_review: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


# 4. Complete input received by Agent 2
class Agent2Input(BaseModel):
    complaint_id: str = Field(min_length=1)
    detected_problems: list[DetectedProblem] = Field(min_length=1)
    jurisdiction: str | None = None
    asset_owner_hints: dict[str, str] = Field(default_factory=dict)
    source_metadata: dict[str, Any] = Field(default_factory=dict)


# 5. Reasons why human review might be needed
class ReviewReason(str, Enum):
    LOW_CONFIDENCE = "low_confidence"
    MISSING_EVIDENCE = "missing_evidence"
    UNKNOWN_CATEGORY = "unknown_category"
    DEPARTMENT_NOT_VERIFIED = "department_not_verified"
    JURISDICTION_UNCLEAR = "jurisdiction_unclear"
    ASSET_OWNER_UNCLEAR = "asset_owner_unclear"
    POLICY_NOT_FOUND = "policy_not_found"
    ELECTRICAL_HAZARD_UNCONFIRMED = (
        "electrical_hazard_unconfirmed"
    )


# 6. Human-review flag for a problem
class ReviewFlag(BaseModel):
    problem_id: str
    reasons: list[ReviewReason] = Field(default_factory=list)
    explanation: str


# 7. Department recommendation for a problem
class DepartmentRecommendation(BaseModel):
    department_id: str | None = None
    department_name: str | None = None
    category: Category
    jurisdiction: str | None = None
    asset_owner: str | None = None
    policy_reference: str | None = None
    verified: bool = False
    rationale: str


# 8. Proposed child ticket
class ChildTicketProposal(BaseModel):
    proposed_ticket_id: str
    parent_complaint_id: str
    problem_ids: list[str] = Field(min_length=1)
    summary: str
    category: Category
    department: DepartmentRecommendation
    severity: Severity = Severity.UNKNOWN
    response_minutes: int | None = Field(default=None, gt=0)
    resolution_minutes: int | None = Field(default=None, gt=0)
    sla_policy_reference: str | None = None
    requires_human_review: bool = False


# 9. Decision for an individual problem
class ProblemDecision(BaseModel):
    problem_id: str
    category: Category
    severity: Severity
    department: DepartmentRecommendation
    rationale: list[str] = Field(default_factory=list)
    review: ReviewFlag | None = None
    proposed_ticket_id: str | None = None


# 10. Final output returned by Agent 2
class Agent2Output(BaseModel):
    complaint_id: str
    status: str
    problem_decisions: list[ProblemDecision]
    child_tickets: list[ChildTicketProposal]
    review_flags: list[ReviewFlag]
    notes: list[str] = Field(default_factory=list)
