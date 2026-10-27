
from schemas import Category, Severity
from policy_retriever import PolicyRetriever


def select_sla(
    category: Category,
    severity: Severity,
    retriever: PolicyRetriever,
) -> tuple[int | None, int | None, str | None]:
    """
    Look up response and resolution targets for a problem.

    Returns:
        response_minutes
        resolution_minutes
        policy_reference

    Returns None values if no matching rule exists.
    """

    rule = retriever.sla_rule(
        category.value,
        severity.value,
    )

    if rule is None:
        return None, None, None

    return (
        rule.get("response_minutes"),
        rule.get("resolution_minutes"),
        rule.get("policy_reference"),
    )
