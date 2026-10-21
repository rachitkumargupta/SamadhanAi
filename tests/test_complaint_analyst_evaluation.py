import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from backend.app.evaluation.complaint_analyst import evaluate


class StubAnalyst:
    def __init__(self, results):
        self.results = iter(results)

    def analyze(self, _input):
        result = next(self.results)
        if isinstance(result, Exception):
            raise result
        return SimpleNamespace(model_dump=lambda mode: result)


class ComplaintAnalystEvaluationTests(unittest.TestCase):
    def test_evaluation_reports_exact_match_and_review_metrics(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "image.jpg").write_bytes(b"approved fixture")
            manifest = root / "cases.jsonl"
            manifest.write_text(
                json.dumps({
                    "id": "review-case",
                    "image": "image.jpg",
                    "expected": {
                        "category": "roads_potholes",
                        "priority_recommendation": "high",
                        "human_review_recommended": True,
                    },
                }) + "\n",
                encoding="utf-8",
            )
            report = evaluate(
                StubAnalyst([{
                    "category": "roads_potholes",
                    "priority_recommendation": "medium",
                    "human_review_recommended": True,
                }]),
                manifest,
            )

        self.assertEqual(report["metrics"]["cases_completed"], 1)
        self.assertEqual(report["metrics"]["field_accuracy"], {
            "category": 1.0,
            "priority_recommendation": 0.0,
            "human_review_recommended": 1.0,
        })
        self.assertEqual(report["metrics"]["human_review_precision"], 1.0)
        self.assertEqual(report["metrics"]["human_review_recall"], 1.0)
        self.assertEqual(report["cases"], [{"id": "review-case", "status": "completed"}])

    def test_evaluation_records_safe_failure_without_leaking_exception_text(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "image.jpg").write_bytes(b"approved fixture")
            manifest = root / "cases.jsonl"
            manifest.write_text(
                json.dumps({"id": "failure-case", "image": "image.jpg", "expected": {"category": "roads_potholes"}}) + "\n",
                encoding="utf-8",
            )
            report = evaluate(StubAnalyst([RuntimeError("private provider detail")]), manifest)

        self.assertEqual(report["metrics"]["provider_or_input_failures"], 1)
        self.assertEqual(report["cases"][0]["status"], "failed")
        self.assertEqual(report["cases"][0]["error_type"], "RuntimeError")
        self.assertNotIn("private provider detail", json.dumps(report))


if __name__ == "__main__":
    unittest.main()
