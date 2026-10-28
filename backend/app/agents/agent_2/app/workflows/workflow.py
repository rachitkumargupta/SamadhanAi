\
from ..agents.routing_agents import RoutingAgent
from ..schemas import ComplaintInput, RoutingProposal
from ..services.human_review_services import HumanReviewService
from ..services.severity_services import SeverityService
from ..services.sla_services import SLAService
from .ticket_splitter import TicketSplitter

class ResolutionWorkflow:
    """Coordinate routing, severity, SLA assessment, and human review."""
    def __init__(self) -> None:
        self.routing_agent = RoutingAgent()
        self.ticket_splitter = TicketSplitter()
        self.severity_service = SeverityService()
        self.sla_service = SLAService()
        self.human_review_service = HumanReviewService()
    def run(self, complaint: ComplaintInput) -> RoutingProposal:
        proposal = self.routing_agent.propose_routing(complaint)
        if not proposal.child_tasks:
            proposal.child_tasks = self.ticket_splitter.split(complaint)
        issues_by_id = {issue.issue_id: issue for issue in complaint.issues}
        for task in proposal.child_tasks:
            task_issues = [
                issues_by_id[issue_id]
                for issue_id in task.issue_ids
                if issue_id in issues_by_id
            ]
            if task_issues:
                severity_results = [
                    self.severity_service.assess(
                        description=issue.description,
                        reported_hazard=issue.reported_hazard,
                    )
                    for issue in task_issues
                ]
                severity_order = {
                    "undetermined": 0,
                    "low": 1,
                    "medium": 2,
                    "high": 3,
                    "critical": 4,
                }
                task.department.severity = max(
                    severity_results,
                    key=lambda severity: severity_order[severity],
                )
            assessment = self.sla_service.assess(
                task.department.policy_evidence
            )
            task.department.completion_timeline = assessment.timeline
            if assessment.requires_human_review:
                task.department.requires_human_review = True
                task.department.review_reason = assessment.reason
        return self.human_review_service.apply(proposal)
