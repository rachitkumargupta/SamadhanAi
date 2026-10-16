"""Provisional complaint lifecycle rules.

The transition table is a code representation of the draft in
docs/architecture/complaint-lifecycle.md. It must be approved before any API
route uses it.
"""

from dataclasses import dataclass
from enum import StrEnum


class ComplaintState(StrEnum):
    SUBMITTED = "submitted"
    NEEDS_INFORMATION = "needs_information"
    UNDER_REVIEW = "under_review"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED_PENDING_VERIFICATION = "resolved_pending_verification"
    CLOSED = "closed"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class TransitionError(ValueError):
    """Base class for a rejected lifecycle transition request."""


class TransitionNotAllowed(TransitionError):
    """The requested state edge is not part of the proposed lifecycle."""


class TransitionUnauthorized(TransitionError):
    """The actor does not meet the proposed role or resource-scope rule."""


class TransitionPreconditionFailed(TransitionError):
    """A required reason, evidence item, or verification is missing."""


@dataclass(frozen=True)
class TransitionContext:
    actor_subject: str
    actor_role: str
    owner_subject: str
    assigned_subject: str | None = None
    reason: str | None = None
    resolution_evidence_present: bool = False
    verification_satisfied: bool = False


@dataclass(frozen=True)
class TransitionRule:
    allowed_roles: frozenset[str]
    requires_owner: bool = False
    requires_assignee: bool = False
    requires_reason: bool = False
    requires_resolution_evidence: bool = False
    requires_verification: bool = False


# Candidate rules only. Role names and the policy itself require team approval.
TRANSITION_RULES: dict[tuple[ComplaintState, ComplaintState], TransitionRule] = {
    (ComplaintState.SUBMITTED, ComplaintState.UNDER_REVIEW): TransitionRule(
        allowed_roles=frozenset({"officer", "supervisor"})
    ),
    (ComplaintState.UNDER_REVIEW, ComplaintState.NEEDS_INFORMATION): TransitionRule(
        allowed_roles=frozenset({"officer", "supervisor"}), requires_reason=True
    ),
    (ComplaintState.NEEDS_INFORMATION, ComplaintState.UNDER_REVIEW): TransitionRule(
        allowed_roles=frozenset({"citizen"}), requires_owner=True
    ),
    (ComplaintState.UNDER_REVIEW, ComplaintState.ASSIGNED): TransitionRule(
        allowed_roles=frozenset({"supervisor"})
    ),
    (ComplaintState.UNDER_REVIEW, ComplaintState.REJECTED): TransitionRule(
        allowed_roles=frozenset({"supervisor"}), requires_reason=True
    ),
    (ComplaintState.ASSIGNED, ComplaintState.IN_PROGRESS): TransitionRule(
        allowed_roles=frozenset({"officer"}), requires_assignee=True
    ),
    (
        ComplaintState.IN_PROGRESS,
        ComplaintState.RESOLVED_PENDING_VERIFICATION,
    ): TransitionRule(
        allowed_roles=frozenset({"officer"}),
        requires_assignee=True,
        requires_resolution_evidence=True,
    ),
    (
        ComplaintState.RESOLVED_PENDING_VERIFICATION,
        ComplaintState.IN_PROGRESS,
    ): TransitionRule(
        allowed_roles=frozenset({"supervisor"}), requires_reason=True
    ),
    (ComplaintState.RESOLVED_PENDING_VERIFICATION, ComplaintState.CLOSED): TransitionRule(
        allowed_roles=frozenset({"supervisor"}),
        requires_verification=True,
    ),
    (ComplaintState.SUBMITTED, ComplaintState.WITHDRAWN): TransitionRule(
        allowed_roles=frozenset({"citizen"}), requires_owner=True, requires_reason=True
    ),
}


def validate_transition(
    current_state: str,
    target_state: str,
    context: TransitionContext,
) -> ComplaintState:
    """Validate a proposed edge and return its normalized target state.

    This checks candidate lifecycle and basic actor-scope conditions only.
    Callers must still enforce current database version, assignment eligibility,
    jurisdiction, policy version, and authorization in the application layer.
    """

    try:
        current = ComplaintState(current_state)
        target = ComplaintState(target_state)
    except (TypeError, ValueError) as exc:
        raise TransitionNotAllowed("Unknown complaint state.") from exc

    rule = TRANSITION_RULES.get((current, target))
    if rule is None:
        raise TransitionNotAllowed(
            f"Transition from {current.value} to {target.value} is not allowed."
        )

    if context.actor_role not in rule.allowed_roles:
        raise TransitionUnauthorized("Actor role cannot request this transition.")
    if rule.requires_owner and context.actor_subject != context.owner_subject:
        raise TransitionUnauthorized("Only the complaint owner can request this transition.")
    if rule.requires_assignee and context.actor_subject != context.assigned_subject:
        raise TransitionUnauthorized("Only the assigned officer can request this transition.")
    if rule.requires_reason and not (context.reason and context.reason.strip()):
        raise TransitionPreconditionFailed("A reason is required for this transition.")
    if rule.requires_resolution_evidence and not context.resolution_evidence_present:
        raise TransitionPreconditionFailed("Resolution evidence is required.")
    if rule.requires_verification and not context.verification_satisfied:
        raise TransitionPreconditionFailed("The verification policy is not satisfied.")

    return target
