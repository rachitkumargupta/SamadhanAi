from uuid import uuid4

from backend.app.agents.agent_2_adapter import run_agent2_for_analysis


def test_agent2_adapter_maps_agent1_category_and_facts_without_visible_evidence():
    complaint_id = uuid4()
    captured = {}

    class FakeWorkflow:
        def run(self, complaint):
            captured["complaint"] = complaint
            return {"proposal": "stub"}

    result = run_agent2_for_analysis(
        complaint_id=complaint_id,
        complaint_text="Original complaint text.",
        location_text="Test location",
        analysis_result={
            "category": "roads",
            "facts": ["A pothole is visible."],
            "visible_evidence": ["Cracked road surface"],
        },
        workflow_factory=FakeWorkflow,
    )

    assert result == {"proposal": "stub"}
    complaint = captured["complaint"]
    assert complaint.complaint_id == str(complaint_id)
    assert complaint.complaint_text == "Original complaint text."
    assert len(complaint.issues) == 1
    assert complaint.issues[0].issue_id == str(complaint_id)
    assert complaint.issues[0].description == "Category: roads; A pothole is visible."
    assert complaint.issues[0].location == "Test location"
    assert complaint.issues[0].reported_hazard is False


def test_agent2_adapter_requires_original_complaint_text():
    try:
        run_agent2_for_analysis(
            complaint_id=uuid4(),
            complaint_text=None,
            location_text=None,
            analysis_result={},
            workflow_factory=lambda: None,
        )
    except ValueError as exc:
        assert str(exc) == "Agent 2 requires the original complaint text."
    else:
        raise AssertionError("Missing complaint text should prevent Agent 2 invocation")
