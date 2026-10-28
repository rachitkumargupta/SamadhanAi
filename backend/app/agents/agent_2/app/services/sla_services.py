
from dataclasses import dataclass
from ..schemas import PolicyEvidence

@dataclass
class SLAAssessment:
    timeline: str | None
    is_verified: bool
    requires_human_review: bool
    reason: str

class SLAService:
    """Assess whether policy evidence supports an official SLA timeline."""
    def assess(self, evidence: list[PolicyEvidence]) -> SLAAssessment:
        verified_evidence = [
            item for item in evidence
            if item.status == "OFFICIAL_VERIFIED"
        ]
        if not verified_evidence:
            return SLAAssessment(
                timeline=None,
                is_verified=False,
                requires_human_review=True,
                reason="No independently verified official policy evidence supports an SLA timeline.",
            )
        return SLAAssessment(
            timeline=None,
            is_verified=True,
            requires_human_review=True,
            reason="Official evidence exists, but an explicit SLA duration must be extracted and validated before assigning a timeline.",
        )
