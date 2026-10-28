"""Map a saved Complaint Analyst result into Agent 2's existing input contract."""

from collections.abc import Callable
from uuid import UUID


def run_agent2_for_analysis(
    *,
    complaint_id: UUID,
    complaint_text: str | None,
    location_text: str | None,
    analysis_result: dict,
    workflow_factory: Callable[[], object] | None = None,
) -> object:
    """Run the existing routing workflow; its proposal is intentionally not persisted."""
    if not complaint_text or not complaint_text.strip():
        raise ValueError("Agent 2 requires the original complaint text.")

    # Lazy imports keep an unavailable Agent 2 dependency/provider from breaking Agent 1.
    from backend.app.agents.agent_2.app.schemas import ComplaintInput, ComplaintIssue

    if workflow_factory is None:
        from backend.app.agents.agent_2.app.workflows.workflow import ResolutionWorkflow

        workflow_factory = ResolutionWorkflow

    category = analysis_result.get("category")
    facts = analysis_result.get("facts") or []
    issue_parts = ([f"Category: {category}"] if category else []) + [
        fact for fact in facts if isinstance(fact, str) and fact.strip()
    ]
    issues = (
        [ComplaintIssue(
            issue_id=str(complaint_id),
            description="; ".join(issue_parts),
            location=location_text,
        )]
        if issue_parts
        else []
    )
    complaint = ComplaintInput(
        complaint_id=str(complaint_id),
        complaint_text=complaint_text,
        issues=issues,
    )
    return workflow_factory().run(complaint)
