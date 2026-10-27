
from schemas import ChildTicketProposal, ProblemDecision


def propose_child_tickets(
    complaint_id: str,
    decisions: list[ProblemDecision],
    sla_by_problem: dict[
        str,
        tuple[int | None, int | None, str | None],
    ],
) -> list[ChildTicketProposal]:
    """
    Propose one child ticket for each detected problem.

    Responsibilities:
    - Preserve the relationship with the parent complaint.
    - Carry department and severity recommendations forward.
    - Use only supplied SLA policy values.
    - Preserve human-review requirements.
    - Never invent missing SLA deadlines.

    Important:
    These are proposals, not persisted database tickets.
    The backend must validate proposals before assignment
    or persistence.
    """

    tickets: list[ChildTicketProposal] = []

    for index, decision in enumerate(decisions, start=1):

        # 1. Get the SLA targets for this problem.
        # Missing rules produce None values, not invented deadlines.
        (
            response_minutes,
            resolution_minutes,
            sla_reference,
        ) = sla_by_problem.get(
            decision.problem_id,
            (None, None, None),
        )

        # 2. Generate a proposal ID.
        # This is not a database-generated ticket ID.
        proposed_ticket_id = f"{complaint_id}-CH-{index}"

        # 3. Create a summary from the existing decision.
        # Do not fabricate details about the complaint.
        summary = (
            decision.rationale[0]
            if decision.rationale
            else f"Review required for problem {decision.problem_id}"
        )

        # 4. Preserve the department recommendation and review status.
        requires_review = decision.review is not None

        ticket = ChildTicketProposal(
            proposed_ticket_id=proposed_ticket_id,
            parent_complaint_id=complaint_id,
            problem_ids=[decision.problem_id],
            summary=summary,
            category=decision.category,
            department=decision.department,
            severity=decision.severity,
            response_minutes=response_minutes,
            resolution_minutes=resolution_minutes,
            sla_policy_reference=sla_reference,
            requires_human_review=requires_review,
        )

        tickets.append(ticket)

    return tickets
