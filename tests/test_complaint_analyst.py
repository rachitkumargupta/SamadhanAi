import unittest
from io import BytesIO

from PIL import Image

from backend.app.agents.complaint_analyst import (
    ANALYSIS_SCHEMA_VERSION,
    AnalystInput,
    AnalystInputError,
    AnalystProviderError,
    AnalysisOutcome,
    ComplaintAnalysis,
    ComplaintAnalyst,
    IssueCategory,
    RecommendationLevel,
    normalize_image,
)


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
        self.assertTrue(provider.args["image_data_url"].startswith("data:image/jpeg;base64,"))

    def test_image_only_requires_grounded_description(self):
        response = completed(generated_description=None)
        with self.assertRaises(AnalystProviderError):
            ComplaintAnalyst(StubProvider(response)).analyze(AnalystInput(image=image_bytes()))

    def test_rejects_non_completed_category_and_invalid_review_flag(self):
        response = completed(outcome=AnalysisOutcome.NEEDS_REVIEW)
        with self.assertRaises(AnalystProviderError):
            ComplaintAnalyst(StubProvider(response)).analyze(
                AnalystInput(image=image_bytes(), description="street issue")
            )

    def test_needs_review_cannot_disable_human_review(self):
        response = completed(
            outcome=AnalysisOutcome.NEEDS_REVIEW,
            category=None,
            human_review_recommended=False,
        )
        with self.assertRaisesRegex(AnalystProviderError, "must recommend human review"):
            ComplaintAnalyst(StubProvider(response)).analyze(
                AnalystInput(image=image_bytes(), description="unclear report")
            )

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

    def test_rejects_category_outside_configured_taxonomy(self):
        analyst = ComplaintAnalyst(
            StubProvider(completed()), allowed_categories={"garbage_sanitation"}
        )
        with self.assertRaisesRegex(AnalystProviderError, "configured taxonomy"):
            analyst.analyze(AnalystInput(image=image_bytes(), description="road damage"))

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
