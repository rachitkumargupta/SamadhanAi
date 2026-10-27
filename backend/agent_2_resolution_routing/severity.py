
from schemas import DetectedProblem, Severity


def assess_severity(
    problem: DetectedProblem,
) -> tuple[Severity, list[str]]:
    """
    Recommend severity using Agent 1's description, evidence,
    and severity hint.

    This is a starter heuristic, not an approved municipal
    severity policy.
    """

    text = " ".join(
        [problem.description, *problem.evidence]
    ).lower()

    reasons: list[str] = []

    # Identify a possible water/electrical interaction.
    electrical_terms = (
        "transformer",
        "electrical equipment",
        "electric wire",
        "power line",
    )

    water_terms = (
        "water",
        "flood",
        "overflow",
        "drain",
        "sewage",
    )

    possible_electrical_risk = (
        any(term in text for term in electrical_terms)
        and any(term in text for term in water_terms)
    )

    if possible_electrical_risk:
        reasons.append(
            "Possible water/electrical interaction; "
            "verify the evidence and follow safety procedures."
        )

        # Preserve an explicitly supplied high-risk hint.
        if problem.severity_hint in (
            Severity.HIGH,
            Severity.CRITICAL,
        ):
            reasons.append(
                "Agent 1 supplied a high-risk severity hint; "
                "validate it against approved policy."
            )
            return problem.severity_hint, reasons

        return Severity.HIGH, reasons

    # Use Agent 1's hint when no special risk rule applies.
    if problem.severity_hint != Severity.UNKNOWN:
        reasons.append(
            "Used Agent 1's severity hint; "
            "validate against approved policy."
        )
        return problem.severity_hint, reasons

    # Basic indicators of potentially serious problems.
    high_risk_terms = (
        "overflowing",
        "blocked drain",
        "road collapsed",
        "exposed live wire",
    )

    if any(term in text for term in high_risk_terms):
        reasons.append(
            "Description indicates potential high impact; "
            "confirm against approved severity policy."
        )
        return Severity.HIGH, reasons

    # Do not invent a severity when evidence is insufficient.
    if problem.confidence < 0.5:
        reasons.append(
            "Confidence is too low for a reliable severity "
            "recommendation."
        )
        return Severity.UNKNOWN, reasons

    reasons.append(
        "No configured severity rule matched; "
        "policy review may be required."
    )
    return Severity.UNKNOWN, reasons
