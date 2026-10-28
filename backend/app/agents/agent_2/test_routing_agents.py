
from backend.app.agents.agent_2.app.agents.routing_agents import RoutingAgent
from backend.app.agents.agent_2.app.schemas import ComplaintInput, ComplaintIssue


def main():
    complaint = ComplaintInput(
        complaint_id="TEST-001",
        complaint_text=(
            "There is a major water leak on the road "
            "and an exposed electrical wire."
        ),
        issues=[
            ComplaintIssue(
                issue_id="ISSUE-1",
                description="Major water leak on the road",
            ),
            ComplaintIssue(
                issue_id="ISSUE-2",
                description="Exposed electrical wire",
                reported_hazard=True,
            ),
        ],
    )

    agent = RoutingAgent()
    proposal = agent.propose_routing(complaint)

    print("\n--- Agent 2 Routing Proposal ---")
    print(proposal.model_dump_json(indent=2))


if __name__ == "__main__":
    main()

