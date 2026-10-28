
from typing import Literal

from pydantic import BaseModel, Field


SeverityLevel = Literal[
    "low",
    "medium",
    "high",
    "critical",
    "undetermined",
]

PolicyStatus = Literal[
    "DRAFT",
    "UNVERIFIED",
    "OFFICIAL_VERIFIED",
]


class ComplaintIssue(BaseModel):
    issue_id: str
    description: str
    location: str | None = None
    reported_hazard: bool = False


class ComplaintInput(BaseModel):
    complaint_id: str
    complaint_text: str
    issues: list[ComplaintIssue] = Field(default_factory=list)


class PolicyEvidence(BaseModel):
    policy_id: str
    title: str
    excerpt: str
    source: str
    status: PolicyStatus = "UNVERIFIED"


class DepartmentProposal(BaseModel):
    department_name: str | None = None
    issue_ids: list[str] = Field(default_factory=list)
    rationale: str
    policy_evidence: list[PolicyEvidence] = Field(default_factory=list)
    severity: SeverityLevel = "undetermined"
    completion_timeline: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    is_provisional: bool = True
    requires_human_review: bool = False
    review_reason: str | None = None


class ChildTaskProposal(BaseModel):
    task_title: str
    issue_ids: list[str] = Field(default_factory=list)
    department: DepartmentProposal


class HazardFlag(BaseModel):
    issue_id: str
    hazard_type: str
    description: str
    urgent_human_attention: bool = True
    requires_human_review: bool = True
    evidence_source: str = "complaint_report"


class RoutingProposal(BaseModel):
    complaint_id: str
    parent_task_title: str
    child_tasks: list[ChildTaskProposal] = Field(default_factory=list)
    hazard_flags: list[HazardFlag] = Field(default_factory=list)
    requires_human_review: bool = False
    human_review_reasons: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
