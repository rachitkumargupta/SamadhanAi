
from app.schemas import ComplaintInput, ChildTaskProposal, DepartmentProposal

class TicketSplitter:
    """Split a complaint into proposed child tasks using structured issues."""
    def split(self, complaint: ComplaintInput) -> list[ChildTaskProposal]:
        child_tasks: list[ChildTaskProposal] = []
        for issue in complaint.issues:
            description = issue.description.strip()
            if not description:
                continue
            task_title = description[:100]
            if len(description) > 100:
                task_title = task_title.rsplit(" ", 1)[0] or description[:100]
            department_proposal = DepartmentProposal(
                department_name=None,
                issue_ids=[issue.issue_id],
                rationale="Separate task proposed for this issue; department jurisdiction must be established using policy evidence.",
                policy_evidence=[],
                severity="undetermined",
                completion_timeline=None,
                confidence=0.0,
                is_provisional=True,
                requires_human_review=True,
                review_reason="Routing, severity, and SLA require further assessment.",
            )
            child_tasks.append(
                ChildTaskProposal(
                    task_title=task_title,
                    issue_ids=[issue.issue_id],
                    department=department_proposal,
                )
            )
        return child_tasks
