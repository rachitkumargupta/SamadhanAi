import unittest
import json
import tempfile
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

from PIL import Image

from backend.app.agents.complaint_analyst import (
    ANALYSIS_SCHEMA_VERSION,
    AnalystInput,
    AnalystInputError,
    AnalystProviderError,
    AnalysisOutcome,
    ConfidenceLevel,
    ComplaintAnalysis,
    ComplaintAnalysisDraft,
    ComplaintAnalyst,
    IssueCategory,
    MissingInformationCode,
    OpenAIResponsesProvider,
    RecommendationLevel,
    AnalystUnavailable,
    build_complaint_analyst,
    normalize_image,
    PriorityFactor,
)
from backend.app.agents.analysis_policy import AnalysisPolicy, AnalysisPolicyError


def image_bytes(fmt="PNG"):
    stream = BytesIO()
    Image.new("RGB", (8, 8), color="gray").save(stream, format=fmt)
    return stream.getvalue()


class StubProvider:
    def __init__(self, response):
        self.response = response
        self.args = None

    def analyze(self, **kwargs):
        self.args = kwargs
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


class StubResponses:
    def __init__(self, parsed=None, error=None):
        self.parsed = parsed
        self.error = error
        self.kwargs = None

    def parse(self, **kwargs):
        self.kwargs = kwargs
        if self.error:
            raise self.error
        return SimpleNamespace(output_parsed=self.parsed)


def completed(**updates):
    values = {
        "schema_version": ANALYSIS_SCHEMA_VERSION,
        "outcome": AnalysisOutcome.COMPLETED,
        "generated_description": "A damaged road surface is visible.",
        "visible_evidence": ["An irregular depression is visible in the road."],
        "facts": ["A road surface is damaged."],
        "inferences": ["The depression may be a pothole."],
        "category": IssueCategory.ROADS_POTHOLES,
        "severity_recommendation": RecommendationLevel.MEDIUM,
        "priority_recommendation": RecommendationLevel.MEDIUM,
        "confidence_level": ConfidenceLevel.HIGH,
        "uncertainty": [],
        "missing_information": [],
        "possible_multi_department": False,
        "human_review_recommended": False,
        "human_review_reasons": [],
    }
    values.update(updates)
    return ComplaintAnalysis.model_validate(values)


class ComplaintAnalystTests(unittest.TestCase):
    def test_text_and_image_return_typed_proposal_with_normalized_image(self):
        provider = StubProvider(completed())
        result = ComplaintAnalyst(provider).analyze(
            AnalystInput(image=image_bytes(), description=" road damage ", location_text=" ward 4 ")
        )
        self.assertEqual(result.category, IssueCategory.ROADS_POTHOLES.value)
        self.assertEqual(provider.args["description"], "road damage")
        self.assertEqual(provider.args["location_text"], "ward 4")
        self.assertIn(IssueCategory.ROADS_POTHOLES.value, provider.args["allowed_categories"])
        self.assertTrue(provider.args["image_data_url"].startswith("data:image/jpeg;base64,"))
        self.assertEqual(provider.args["category_descriptions"][IssueCategory.ROADS_POTHOLES.value],
                         AnalysisPolicy.load().taxonomy[IssueCategory.ROADS_POTHOLES.value])

    def test_same_draft_and_policy_produce_identical_classification_and_priority(self):
        draft = completed(
            priority_factors=[PriorityFactor(
                criterion="service_disruption",
                evidence="An irregular depression is visible in the road.",
            )]
        )
        first = ComplaintAnalyst(StubProvider(draft)).analyze(
            AnalystInput(image=image_bytes(), description="Road damage", location_text="Ward 4")
        )
        second = ComplaintAnalyst(StubProvider(draft)).analyze(
            AnalystInput(image=image_bytes(), description="Road damage", location_text="Ward 4")
        )
        self.assertEqual(first.model_dump(), second.model_dump())
        self.assertEqual(first.category, IssueCategory.ROADS_POTHOLES.value)
        self.assertEqual(first.priority_recommendation, RecommendationLevel.MEDIUM)
        self.assertEqual(first.priority_score, 1)
        self.assertFalse(first.human_review_recommended)

    def test_priority_rules_are_explainable_and_hazard_never_becomes_automatic_critical(self):
        draft = completed(
            priority_recommendation=RecommendationLevel.CRITICAL,
            priority_factors=[PriorityFactor(
                criterion="potential_safety_hazard",
                evidence="An irregular depression is visible in the road.",
            )],
        )
        result = ComplaintAnalyst(StubProvider(draft)).analyze(
            AnalystInput(image=image_bytes(), description="Road damage", location_text="Ward 4")
        )
        self.assertEqual(result.priority_recommendation, RecommendationLevel.HIGH)
        self.assertEqual(result.model_priority_recommendation, RecommendationLevel.CRITICAL)
        self.assertIn("potential_safety_hazard", result.priority_criteria)
        self.assertTrue(any("potential_safety_hazard:" in item for item in result.priority_explanation))
        self.assertTrue(result.human_review_recommended)
        self.assertIn("potential_hazard_requires_human_triage", result.human_review_reasons)

    def test_potential_hazard_report_term_triggers_high_provisional_priority_and_review(self):
        draft = completed(priority_factors=[])
        result = ComplaintAnalyst(StubProvider(draft)).analyze(
            AnalystInput(
                image=image_bytes(),
                description="There is an exposed wire by the sidewalk.",
                location_text="Ward 4",
            )
        )
        self.assertEqual(result.priority_recommendation, RecommendationLevel.HIGH)
        self.assertTrue(result.human_review_recommended)
        self.assertIn("potential_safety_hazard", result.priority_criteria)
        self.assertTrue(any(
            factor.criterion == "potential_safety_hazard"
            and factor.evidence_source == "citizen_description"
            for factor in result.priority_factors
        ))

    def test_unsupported_priority_evidence_is_not_counted_and_requires_review(self):
        draft = completed(priority_factors=[PriorityFactor(
            criterion="public_access_obstructed", evidence="A bridge is completely blocked."
        )])
        result = ComplaintAnalyst(StubProvider(draft)).analyze(
            AnalystInput(image=image_bytes(), description="Road damage", location_text="Ward 4")
        )
        self.assertEqual(result.priority_score, 0)
        self.assertEqual(result.priority_recommendation, RecommendationLevel.LOW)
        self.assertTrue(result.human_review_recommended)
        self.assertIn("unsupported_priority_evidence", result.human_review_reasons)

    def test_unclear_image_produces_insufficient_context_and_no_priority(self):
        draft = completed(visible_evidence=[], facts=[], priority_recommendation=RecommendationLevel.HIGH)
        result = ComplaintAnalyst(StubProvider(draft)).analyze(
            AnalystInput(image=image_bytes(), description="Something is wrong", location_text="Ward 4")
        )
        self.assertEqual(result.outcome, AnalysisOutcome.INSUFFICIENT_CONTEXT)
        self.assertEqual(result.category, IssueCategory.OTHER_UNCERTAIN.value)
        self.assertIsNone(result.priority_recommendation)
        self.assertTrue(result.human_review_recommended)
        self.assertIn("insufficient_visual_evidence", result.human_review_reasons)
        self.assertIn(MissingInformationCode.CLEARER_IMAGE, result.missing_information_codes)

    def test_missing_location_is_reported_without_blocking_image_classification(self):
        result = ComplaintAnalyst(StubProvider(completed())).analyze(
            AnalystInput(image=image_bytes(), description="Road damage")
        )
        self.assertEqual(result.category, IssueCategory.ROADS_POTHOLES.value)
        self.assertIn("missing_location", result.human_review_reasons)
        self.assertIn(MissingInformationCode.LOCATION, result.missing_information_codes)
        self.assertTrue(result.human_review_recommended)

    def test_medium_or_low_self_reported_confidence_requires_review(self):
        for confidence in (ConfidenceLevel.MEDIUM, ConfidenceLevel.LOW):
            with self.subTest(confidence=confidence):
                result = ComplaintAnalyst(StubProvider(completed(confidence_level=confidence))).analyze(
                    AnalystInput(image=image_bytes(), description="Road damage", location_text="Ward 4")
                )
                self.assertEqual(result.outcome, AnalysisOutcome.NEEDS_REVIEW)
                self.assertIn("non_high_self_reported_confidence", result.human_review_reasons)

    def test_image_only_without_grounded_description_is_reviewable_insufficient_context(self):
        response = completed(generated_description=None)
        result = ComplaintAnalyst(StubProvider(response)).analyze(AnalystInput(image=image_bytes()))
        self.assertEqual(result.outcome, AnalysisOutcome.INSUFFICIENT_CONTEXT)
        self.assertTrue(result.human_review_recommended)
        self.assertIn(MissingInformationCode.ADDITIONAL_ISSUE_DETAILS, result.missing_information_codes)

    def test_policy_overrides_model_attempt_to_disable_review(self):
        response = completed(
            outcome=AnalysisOutcome.NEEDS_REVIEW,
            category=None,
            human_review_recommended=False,
        )
        result = ComplaintAnalyst(StubProvider(response)).analyze(
            AnalystInput(image=image_bytes(), description="street issue", location_text="Ward 4")
        )
        self.assertEqual(result.outcome, AnalysisOutcome.NEEDS_REVIEW)
        self.assertTrue(result.human_review_recommended)

    def test_needs_review_can_preserve_a_category_proposal(self):
        response = completed(
            outcome=AnalysisOutcome.NEEDS_REVIEW,
            human_review_recommended=True,
        )
        result = ComplaintAnalyst(StubProvider(response)).analyze(
            AnalystInput(image=image_bytes(), description="unclear report")
        )
        self.assertEqual(result.category, IssueCategory.ROADS_POTHOLES.value)
        self.assertTrue(result.human_review_recommended)

    def test_insufficient_context_is_an_explicit_result(self):
        response = completed(
            outcome=AnalysisOutcome.INSUFFICIENT_CONTEXT,
            category=None,
            human_review_recommended=True,
            missing_information=["A clearer image is needed."],
        )
        result = ComplaintAnalyst(StubProvider(response)).analyze(
            AnalystInput(image=image_bytes(), description="Something is wrong")
        )
        self.assertEqual(result.outcome, AnalysisOutcome.INSUFFICIENT_CONTEXT)

    def test_uncertainty_and_critical_recommendation_require_human_review(self):
        result = ComplaintAnalyst(
            StubProvider(
                completed(
                    uncertainty=["The image does not clearly show the full issue."],
                    human_review_recommended=False,
                    priority_recommendation=RecommendationLevel.CRITICAL,
                )
            )
        ).analyze(AnalystInput(image=image_bytes(), description="street issue"))
        self.assertTrue(result.human_review_recommended)
        self.assertTrue(result.human_review_reasons)

    def test_provider_failure_is_not_replaced_by_fake_result(self):
        with self.assertRaisesRegex(AnalystProviderError, "RuntimeError"):
            ComplaintAnalyst(StubProvider(RuntimeError("provider unavailable"))).analyze(
                AnalystInput(image=image_bytes(), description="street issue")
            )

    def test_openai_adapter_uses_structured_non_stored_image_request(self):
        responses = StubResponses(parsed=completed())
        provider = OpenAIResponsesProvider(
            api_key="test-key",
            model="vision-test-model",
            client=SimpleNamespace(responses=responses),
        )
        result = provider.analyze(
            image_data_url="data:image/jpeg;base64,ZmFrZQ==",
            description="A road defect",
            location_text="Ward 4",
        )
        self.assertEqual(result.category, IssueCategory.ROADS_POTHOLES.value)
        self.assertFalse(responses.kwargs["store"])
        self.assertEqual(responses.kwargs["max_output_tokens"], 1200)
        self.assertIs(responses.kwargs["text_format"], ComplaintAnalysisDraft)
        self.assertEqual(responses.kwargs["input"][1]["content"][1]["type"], "input_image")

    def test_openai_adapter_wraps_transport_errors_and_empty_output(self):
        for responses in (StubResponses(error=TimeoutError()), StubResponses(parsed=None)):
            with self.subTest(responses=responses), self.assertRaises(AnalystProviderError):
                OpenAIResponsesProvider(
                    api_key="test-key",
                    model="vision-test-model",
                    client=SimpleNamespace(responses=responses),
                ).analyze(image_data_url="data:image/jpeg;base64,AA==", description=None, location_text=None)

    def test_installed_openai_sdk_builds_structured_request_without_external_network(self):
        import httpx
        from openai import OpenAI

        captured = {}

        def respond(request):
            captured.update(json.loads(request.content))
            return httpx.Response(503, request=request, json={"error": {"message": "stubbed"}})

        client = OpenAI(
            api_key="test-key",
            max_retries=0,
            http_client=httpx.Client(transport=httpx.MockTransport(respond)),
        )
        try:
            provider = OpenAIResponsesProvider(
                api_key="test-key", model="gpt-6-luna", client=client
            )
            with self.assertRaises(AnalystProviderError):
                provider.analyze(
                    image_data_url="data:image/jpeg;base64,AA==",
                    description="A road issue",
                    location_text=None,
                )
        finally:
            client.close()
        self.assertFalse(captured["store"])
        self.assertEqual(captured["max_output_tokens"], 1200)
        self.assertEqual(captured["text"]["format"]["type"], "json_schema")
        self.assertIn("contradictory_information", captured["text"]["format"]["schema"]["properties"])

    def test_missing_credentials_are_explicit(self):
        settings = SimpleNamespace(
            openai_api_key=None,
            complaint_analyst_model="vision-test-model",
            complaint_analyst_timeout_seconds=1,
            complaint_analyst_categories="roads_potholes",
        )
        with self.assertRaises(AnalystUnavailable):
            build_complaint_analyst(settings)

    def test_rejects_category_outside_configured_taxonomy(self):
        analyst = ComplaintAnalyst(
            StubProvider(completed()), allowed_categories={"garbage_sanitation", "other_uncertain"}
        )
        result = analyst.analyze(AnalystInput(
            image=image_bytes(), description="road damage", location_text="Ward 4"
        ))
        self.assertEqual(result.category, IssueCategory.OTHER_UNCERTAIN.value)
        self.assertTrue(result.human_review_recommended)

    def test_default_policy_has_nonempty_taxonomy_and_explicit_priority_bands(self):
        policy = AnalysisPolicy.load()
        self.assertIn(IssueCategory.OTHER_UNCERTAIN.value, policy.taxonomy)
        self.assertEqual(policy.assess_priority([]).recommendation, "low")
        self.assertEqual(policy.assess_priority(["service_disruption"]).recommendation, "medium")
        self.assertEqual(policy.assess_priority(["public_access_obstructed"]).recommendation, "high")

    def test_policy_json_can_be_revised_without_changing_agent_code(self):
        policy_path = Path(__file__).parents[1] / "backend" / "app" / "agents" / "analysis_policy.json"
        policy_data = json.loads(policy_path.read_text(encoding="utf-8"))
        policy_data["priority"]["criteria"]["service_disruption"]["points"] = 2
        policy_data["version"] = "team-approved-candidate-2"
        with tempfile.TemporaryDirectory() as temp_dir:
            override_path = Path(temp_dir) / "policy.json"
            override_path.write_text(json.dumps(policy_data), encoding="utf-8")
            policy = AnalysisPolicy.load(override_path)
        self.assertEqual(policy.version, "team-approved-candidate-2")
        self.assertEqual(policy.assess_priority(["service_disruption"]).recommendation, "high")

    def test_policy_rejects_empty_taxonomy_instead_of_running_unconfigured(self):
        policy_path = Path(__file__).parents[1] / "backend" / "app" / "agents" / "analysis_policy.json"
        policy_data = json.loads(policy_path.read_text(encoding="utf-8"))
        policy_data["taxonomy"] = {}
        with tempfile.TemporaryDirectory() as temp_dir:
            override_path = Path(temp_dir) / "empty-policy.json"
            override_path.write_text(json.dumps(policy_data), encoding="utf-8")
            with self.assertRaises(AnalysisPolicyError):
                AnalysisPolicy.load(override_path)

    def test_policy_cannot_disable_hazard_review_or_lower_hazard_below_high(self):
        policy_path = Path(__file__).parents[1] / "backend" / "app" / "agents" / "analysis_policy.json"
        original = json.loads(policy_path.read_text(encoding="utf-8"))
        invalid_variants = []
        no_review = json.loads(json.dumps(original))
        no_review["priority"]["human_review_criteria"] = []
        invalid_variants.append(no_review)
        too_low = json.loads(json.dumps(original))
        too_low["priority"]["criteria"]["potential_safety_hazard"]["points"] = 1
        invalid_variants.append(too_low)
        for index, policy_data in enumerate(invalid_variants):
            with self.subTest(policy=index), tempfile.TemporaryDirectory() as temp_dir:
                override_path = Path(temp_dir) / "unsafe-policy.json"
                override_path.write_text(json.dumps(policy_data), encoding="utf-8")
                with self.assertRaises(AnalysisPolicyError):
                    AnalysisPolicy.load(override_path)

    def test_policy_requires_explicit_nonempty_provenance(self):
        policy_path = Path(__file__).parents[1] / "backend" / "app" / "agents" / "analysis_policy.json"
        policy_data = json.loads(policy_path.read_text(encoding="utf-8"))
        policy_data["approval_status"] = ""
        with tempfile.TemporaryDirectory() as temp_dir:
            override_path = Path(temp_dir) / "unlabeled-policy.json"
            override_path.write_text(json.dumps(policy_data), encoding="utf-8")
            with self.assertRaises(AnalysisPolicyError):
                AnalysisPolicy.load(override_path)

    def test_explicit_empty_allowed_category_set_is_rejected(self):
        with self.assertRaises(AnalysisPolicyError):
            ComplaintAnalyst(StubProvider(completed()), allowed_categories=set())

    def test_rejects_unsupported_or_non_image_content(self):
        for raw in (b"", b"not an image"):
            with self.subTest(raw=raw), self.assertRaises(AnalystInputError):
                normalize_image(raw)

    def test_normalization_strips_source_format_and_metadata(self):
        normalized, mime = normalize_image(image_bytes("WEBP"))
        self.assertEqual(mime, "image/jpeg")
        with Image.open(BytesIO(normalized)) as decoded:
            self.assertEqual(decoded.format, "JPEG")
            self.assertEqual(decoded.size, (8, 8))


if __name__ == "__main__":
    unittest.main()
