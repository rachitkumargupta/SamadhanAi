
from dataclasses import dataclass, field
from app.schemas import RoutingProposal

@dataclass
class HumanReviewDecision:
    required: bool
    reasons: list[str] = field(default_factory=list)

class HumanReviewService:
    """Determine whether a routing proposal needs human review."""
    def assess(self, proposal: RoutingProposal) -> HumanReviewDecision:
        reasons: list[str] = []
        if proposal.requires_human_review:
            reasons.extend(proposal.human_review_reasons)
        for task in proposal.child_tasks:
            department = task.department
            if department.requires_human_review:
                reason = department.review_reason or (
                    f"Human review is required for task: {task.task_title}."
                )
                reasons.append(reason)
            if department.is_provisional:
                reasons.append(
                    f"Department recommendation is provisional for task: {task.task_title}."
                )
            if department.severity == "undetermined":
                reasons.append(
                    f"Severity is undetermined for task: {task.task_title}."
                )
            if not department.policy_evidence:
                reasons.append(
                    f"Policy evidence is missing for task: {task.task_title}."
                )
        for hazard in proposal.hazard_flags:
            if hazard.requires_human_review:
                reasons.append(
                    f"Reported hazard requires review for issue {hazard.issue_id}: {hazard.description}"
                )
        unique_reasons = list(dict.fromkeys(reason for reason in reasons if reason.strip()))
        return HumanReviewDecision(
            required=bool(unique_reasons),
            reasons=unique_reasons,
        )
    def apply(self, proposal: RoutingProposal) -> RoutingProposal:
        decision = self.assess(proposal)
        proposal.requires_human_review = decision.required
        proposal.human_review_reasons = decision.reasons
        return proposal
