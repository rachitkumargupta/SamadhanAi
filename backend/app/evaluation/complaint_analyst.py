"""Run a deliberately small, human-labeled Complaint Analyst evaluation set.

This tool reports measurements but does not decide whether the agent passes.
Evaluation examples are sent to the configured model provider, so invocation
requires an explicit acknowledgement that the dataset is approved for that use.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from backend.app.agents.complaint_analyst import AnalystInput, build_complaint_analyst
from backend.app.config import get_settings


def _load_manifest(path: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        try:
            case = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON on manifest line {line_number}.") from exc
        if not isinstance(case, dict) or not isinstance(case.get("expected"), dict):
            raise ValueError(f"Manifest line {line_number} must contain an object and expected object.")
        if not isinstance(case.get("image"), str) or not case["image"].strip():
            raise ValueError(f"Manifest line {line_number} must include an image path.")
        expected = case["expected"]
        supported = {"category", "priority_recommendation", "severity_recommendation", "human_review_recommended"}
        if not (set(expected) & supported):
            raise ValueError(f"Manifest line {line_number} needs at least one supported expected field.")
        cases.append(case)
    if not cases:
        raise ValueError("The evaluation manifest contains no cases.")
    return cases


def _record_match(counts: Counter[str], field: str, expected: dict, actual: dict) -> None:
    if field not in expected:
        return
    counts[f"{field}_total"] += 1
    counts[f"{field}_correct"] += expected[field] == actual.get(field)


def _evaluate_case(analyst, manifest_path: Path, case: dict) -> tuple[dict[str, Any], dict[str, Any] | None]:
    case_id = str(case.get("id") or f"case-{case.get('_line', '?')}")[:100]
    expected = case["expected"]
    try:
        image_path = (manifest_path.parent / case["image"]).resolve()
        image = image_path.read_bytes()
        result = analyst.analyze(
            AnalystInput(
                image=image,
                description=case.get("description"),
                location_text=case.get("location_text"),
            )
        ).model_dump(mode="json")
        return {"id": case_id, "status": "completed"}, {"expected": expected, "actual": result}
    except Exception as exc:  # Report a safe class name; never print image/provider content.
        return {"id": case_id, "status": "failed", "error_type": type(exc).__name__}, None


def evaluate(analyst, manifest_path: Path) -> dict[str, Any]:
    cases = _load_manifest(manifest_path)
    outcomes: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    review_tp = review_fp = review_fn = 0
    for line_number, case in enumerate(cases, 1):
        case["_line"] = line_number
        outcome, scored = _evaluate_case(analyst, manifest_path, case)
        outcomes.append(outcome)
        if scored is None:
            counts["provider_or_input_failures"] += 1
            continue
        expected, actual = scored["expected"], scored["actual"]
        for field in (
            "category",
            "priority_recommendation",
            "severity_recommendation",
            "human_review_recommended",
        ):
            _record_match(counts, field, expected, actual)
        if "human_review_recommended" in expected:
            predicted = bool(actual.get("human_review_recommended"))
            required = bool(expected["human_review_recommended"])
            review_tp += predicted and required
            review_fp += predicted and not required
            review_fn += not predicted and required

    metrics = {
        "cases_total": len(cases),
        "cases_completed": sum(item["status"] == "completed" for item in outcomes),
        "provider_or_input_failures": counts["provider_or_input_failures"],
        "field_accuracy": {
            key.removesuffix("_total"): counts[key.removesuffix("_total") + "_correct"] / total
            for key, total in counts.items()
            if key.endswith("_total") and total
        },
        "human_review_precision": review_tp / (review_tp + review_fp) if review_tp + review_fp else None,
        "human_review_recall": review_tp / (review_tp + review_fn) if review_tp + review_fn else None,
    }
    return {"metrics": metrics, "cases": outcomes}


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate Complaint Analyst against a labeled JSONL manifest.")
    parser.add_argument("manifest", type=Path, help="JSONL manifest with image paths and expected labels")
    parser.add_argument(
        "--allow-provider-processing",
        action="store_true",
        help="Acknowledge that this dataset is approved to be processed by the configured provider.",
    )
    args = parser.parse_args()
    if not args.allow_provider_processing:
        parser.error("provider processing requires --allow-provider-processing and approved evaluation data")
    try:
        report = evaluate(build_complaint_analyst(get_settings()), args.manifest.resolve())
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    json.dump(report, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
