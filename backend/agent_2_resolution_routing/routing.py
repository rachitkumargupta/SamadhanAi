
from policy_retriever import PolicyRetriever
from review import (
    review_problem,
    requires_human_classification,
)
from schemas import (
    Agent2Input,
    Agent2Output,
    DepartmentRecommendation,
    ProblemDecision,
    ReviewFlag,
)
from severity import assess_severity
from sla import select_sla
from ticket_splitter import propose_child_tickets


class ResolutionRoutingAgent:
    """
    Main orchestration class for Samadhan AI Agent 2.

    Receives detected problems from Agent 1 and produces
    routing recommendations and proposed child tickets.

    Agent 2 proposes decisions only. The backend must validate
    all recommendations before persisting them.
    """

    def __init__(
        self,
        retriever: PolicyRetriever | None = None,
    ):
        self.retriever = retriever or PolicyRetriever()

    def run(self, payload: Agent2Input) -> Agent2Output:
        """
        Process each detected problem independently.

        Uncertain classifications are flagged for human review.
        No category-specific SLA is proposed for uncertain cases.
        """

        decisions = []
        sla_by_problem = {}
        review_flags = []

        notes = [
            "Agent 2 produces proposals; the backend must "
            "validate decisions before persistence.",
            "Agent 2 does not start or monitor SLA clocks.",
            "Uncertain classifications require human review.",
            "Demo routing and SLA data are not official policies.",
        ]

        if self.retriever.is_demo_data:
            notes.append(
                "Demo reference data is being used. "
                "Department mappings and SLA values must not "
                "be treated as verified municipal requirements."
            )

        # Process every problem independently.
        for problem in payload.detected_problems:

            # 1. Check whether classification is reliable enough
            # to proceed with normal department routing.
            classification_reasons = (
                requires_human_classification(problem)
            )
            classification_uncertain = bool(
                classification_reasons
            )

            # 2. Look up a department only when classification
            # does not trigger the human-review gate.
            rule = None

            if not classification_uncertain:
                rule = self.retriever.department_rule(
                    problem.category.value
                )

            if rule is not None:
                department = DepartmentRecommendation(
                    department_id=rule.get("department_id"),
                    department_name=rule.get("department_name"),
                    category=problem.category,
                    jurisdiction=payload.jurisdiction,
                    asset_owner=payload.asset_owner_hints.get(
                        problem.problem_id
                    ),
                    policy_reference=rule.get("policy_reference"),
                    verified=bool(rule.get("verified", False)),
                    rationale=(
                        "Matched a configured category mapping. "
                        "Jurisdiction and asset ownership must "
                        "still be validated."
                    ),
                )
            else:
                # Never invent a department when classification
                # is uncertain or no category mapping exists.
                department = DepartmentRecommendation(
                    category=problem.category,
                    jurisdiction=payload.jurisdiction,
                    asset_owner=payload.asset_owner_hints.get(
                        problem.problem_id
                    ),
                    verified=False,
                    rationale=(
                        "No department recommendation was made "
                        "because classification is uncertain or "
                        "no department mapping was found. "
                        "Human review is required."
                    ),
                )

            # 3. Recommend severity using the existing heuristic.
            severity, severity_reasons = assess_severity(problem)

            # 4. Run the existing review checks for department,
            # jurisdiction, evidence, policy and hazard uncertainty.
            review = review_problem(
                problem=problem,
                department=department,
                jurisdiction_supplied=bool(payload.jurisdiction),
                demo_policy_data=self.retriever.is_demo_data,
            )

            # 5. Merge classification review reasons with other
            # review reasons without creating duplicate entries.
            if classification_reasons:
                if review is None:
                    review = ReviewFlag(
                        problem_id=problem.problem_id,
                        reasons=classification_reasons,
                        explanation=(
                            "Classification is uncertain. "
                            "Human review is required before "
                            "department assignment."
                        ),
                    )
                else:
                    review.reasons = list(
                        dict.fromkeys(
                            review.reasons + classification_reasons
                        )
                    )
                    review.explanation = (
                        "Human review required: "
                        + ", ".join(
                            reason.value for reason in review.reasons
                        )
                    )

            if review is not None:
                review_flags.append(review)

            # 6. Build the decision for this problem.
            decision = ProblemDecision(
                problem_id=problem.problem_id,
                category=problem.category,
                severity=severity,
                department=department,
                rationale=severity_reasons + [department.rationale],
                review=review,
            )
            decisions.append(decision)

            # 7. Do not look up a category-specific SLA if
            # classification is uncertain.
            if classification_uncertain:
                sla_by_problem[problem.problem_id] = {
                    "response_minutes": None,
                    "resolution_minutes": None,
                    "policy_reference": None,
                }
            else:
                sla_by_problem[problem.problem_id] = select_sla(
                    category=problem.category,
                    severity=severity,
                    retriever=self.retriever,
                )

        # 8. Propose child tickets for all detected problems,
        # including those requiring human review.
        child_tickets = propose_child_tickets(
            complaint_id=payload.complaint_id,
            decisions=decisions,
            sla_by_problem=sla_by_problem,
        )

        # 9. Link each decision to its proposed child ticket.
        for decision, ticket in zip(decisions, child_tickets):
            decision.proposed_ticket_id = (
                ticket.proposed_ticket_id
            )

        # 10. Determine the overall result status.
        status = (
            "needs_human_review"
            if review_flags
            else "ready_for_backend_validation"
        )

        return Agent2Output(
            complaint_id=payload.complaint_id,
            status=status,
            problem_decisions=decisions,
            child_tickets=child_tickets,
            review_flags=review_flags,
            notes=notes,
        )
