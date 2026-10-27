
from schemas import (
    Category,
    DetectedProblem,
    DepartmentRecommendation,
    ReviewFlag,
    ReviewReason,
)


def review_problem(
    problem: DetectedProblem,
    department: DepartmentRecommendation,
    jurisdiction_supplied: bool,
    demo_policy_data: bool,
) -> ReviewFlag | None:
    """
    Check whether a problem needs human review.

    Returns a ReviewFlag if review is needed.
    Returns None if none of these checks trigger review.
    """

    reasons = []

    # 1. Check confidence from Agent 1.
    if problem.confidence < 0.7:
        reasons.append(ReviewReason.LOW_CONFIDENCE)

    # 2. Check whether evidence was provided.
    if not problem.evidence:
        reasons.append(ReviewReason.MISSING_EVIDENCE)

    # 3. Check whether the problem category is known.
    if problem.category == Category.UNKNOWN:
        reasons.append(ReviewReason.UNKNOWN_CATEGORY)

    # 4. Check whether the department mapping is verified.
    if not department.verified:
        reasons.append(ReviewReason.DEPARTMENT_NOT_VERIFIED)

    # 5. Check whether jurisdiction is known.
    if not jurisdiction_supplied:
        reasons.append(ReviewReason.JURISDICTION_UNCLEAR)

    # 6. Respect an existing review flag from Agent 1.
    if problem.requires_human_review:
        reasons.append(ReviewReason.ASSET_OWNER_UNCLEAR)

    # 7. Demo configuration is not an approved policy source.
    if demo_policy_data:
        reasons.append(ReviewReason.POLICY_NOT_FOUND)

    # 8. Check for an unconfirmed electrical hazard.
    text = " ".join(
        [problem.description, *problem.evidence]
    ).lower()

    if (
        problem.category == Category.STREETLIGHTS_ELECTRICAL
        and any(word in text for word in ("water", "drain", "flood"))
    ):
        contact_evidence = (
            "contact",
            "touching",
            "reaching",
            "immersed",
        )

        if not any(word in text for word in contact_evidence):
            reasons.append(
                ReviewReason.ELECTRICAL_HAZARD_UNCONFIRMED
            )

    # Remove duplicate reasons while preserving their order.
    reasons = list(dict.fromkeys(reasons))

    if not reasons:
        return None

    return ReviewFlag(
        problem_id=problem.problem_id,
        reasons=reasons,
        explanation=(
            "Human review required: "
            + ", ".join(reason.value for reason in reasons)
        ),
    )
def requires_human_classification(
    problem: DetectedProblem,
    confidence_threshold: float = 0.7,
) -> list[ReviewReason]:
    reasons = []

    if problem.category == Category.UNKNOWN:
        reasons.append(ReviewReason.UNKNOWN_CATEGORY)

    if problem.confidence < confidence_threshold:
        reasons.append(ReviewReason.LOW_CONFIDENCE)

    if not problem.evidence:
        reasons.append(ReviewReason.MISSING_EVIDENCE)

    if problem.requires_human_review:
        reasons.append(ReviewReason.ASSET_OWNER_UNCLEAR)

    return list(dict.fromkeys(reasons))