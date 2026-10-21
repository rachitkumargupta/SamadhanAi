"""Loadable, versioned policy defaults for the Complaint Analyst MVP.

The checked-in policy is a provisional engineering rubric, not a municipal rule.
Deployments can replace it with an approved JSON policy without changing agent code.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class AnalysisPolicyError(ValueError):
    """The configured analyst policy is empty, invalid, or internally inconsistent."""


@dataclass(frozen=True)
class PriorityAssessment:
    recommendation: str | None
    score: int
    criteria: tuple[str, ...]
    explanation: tuple[str, ...]
    human_review_required: bool


@dataclass(frozen=True)
class PotentialHazardSignal:
    source: str
    evidence: str


@dataclass(frozen=True)
class AnalysisPolicy:
    policy_id: str
    version: str
    approval_status: str
    taxonomy: dict[str, str]
    fallback_category: str
    priority_criteria: dict[str, dict[str, Any]]
    low_max: int
    medium_max: int
    high_min: int
    automatic_critical: bool
    human_review_criteria: frozenset[str]
    potential_hazard_terms: tuple[str, ...]

    @classmethod
    def load(cls, path: str | Path | None = None, *, category_override: str | None = None) -> "AnalysisPolicy":
        policy_path = Path(path) if path else Path(__file__).with_name("analysis_policy.json")
        try:
            raw = json.loads(policy_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise AnalysisPolicyError(f"Cannot load Complaint Analyst policy file: {policy_path}") from exc
        try:
            taxonomy = raw["taxonomy"]
            priority = raw["priority"]
            criteria = priority["criteria"]
            thresholds = priority["thresholds"]
            fallback = raw["fallback_category"]
            for field in ("policy_id", "version", "approval_status"):
                if not isinstance(raw.get(field), str) or not raw[field].strip():
                    raise ValueError(f"{field} must be a non-empty string")
            if not isinstance(taxonomy, dict) or not taxonomy:
                raise ValueError("taxonomy must be a non-empty object")
            if any(not isinstance(key, str) or not key.strip() or not isinstance(value, str) or not value.strip()
                   for key, value in taxonomy.items()):
                raise ValueError("taxonomy IDs and descriptions must be non-empty strings")
            if fallback not in taxonomy:
                raise ValueError("fallback_category must exist in taxonomy")
            if not isinstance(criteria, dict) or not criteria:
                raise ValueError("priority criteria must be a non-empty object")
            for key, item in criteria.items():
                if (not isinstance(key, str) or not key.strip() or not isinstance(item, dict)
                        or type(item.get("points")) is not int or item["points"] < 0
                        or not isinstance(item.get("description"), str) or not item["description"].strip()):
                    raise ValueError("each priority criterion needs a string description and non-negative integer points")
            low_max = thresholds["low_max"]
            medium_max = thresholds["medium_max"]
            high_min = thresholds["high_min"]
            if not (type(low_max) is int and type(medium_max) is int and type(high_min) is int
                    and 0 <= low_max <= medium_max and high_min == medium_max + 1):
                raise ValueError("priority thresholds must be contiguous: 0 <= low_max <= medium_max and high_min = medium_max + 1")
            if priority.get("automatic_critical", False) is not False:
                raise ValueError("automatic critical priority is disabled in the MVP safety baseline")
            hazard_terms = priority.get("potential_hazard_terms", [])
            if not isinstance(hazard_terms, list) or any(not isinstance(term, str) or not term.strip() for term in hazard_terms):
                raise ValueError("potential_hazard_terms must be a list of non-empty strings")
            review_criteria = priority.get("human_review_criteria", [])
            if not isinstance(review_criteria, list) or any(item not in criteria for item in review_criteria):
                raise ValueError("human_review_criteria must refer to configured priority criteria")
            hazard_criterion = criteria.get("potential_safety_hazard")
            if hazard_criterion is None:
                raise ValueError("potential_safety_hazard criterion is required for safe hazard handling")
            if hazard_criterion["points"] < high_min:
                raise ValueError("potential_safety_hazard must reach the configured high priority band")
            if "potential_safety_hazard" not in review_criteria:
                raise ValueError("potential_safety_hazard must always require human review")
            if category_override:
                selected = {item.strip() for item in category_override.split(",") if item.strip()}
                unknown = selected - set(taxonomy)
                if not selected or unknown or fallback not in selected:
                    raise ValueError("category override must be non-empty, known, and include the fallback category")
                taxonomy = {key: value for key, value in taxonomy.items() if key in selected}
        except (KeyError, TypeError, ValueError) as exc:
            raise AnalysisPolicyError(f"Invalid Complaint Analyst policy: {exc}") from exc

        return cls(
            policy_id=str(raw.get("policy_id", "complaint_analyst")),
            version=str(raw.get("version", "unversioned")),
            approval_status=str(raw.get("approval_status", "unapproved")),
            taxonomy=dict(taxonomy),
            fallback_category=fallback,
            priority_criteria=dict(criteria),
            low_max=low_max,
            medium_max=medium_max,
            high_min=high_min,
            automatic_critical=bool(priority.get("automatic_critical", False)),
            human_review_criteria=frozenset(review_criteria),
            potential_hazard_terms=tuple(hazard_terms),
        )

    def find_potential_hazard(self, *, description: str | None, visible_evidence: list[str]) -> PotentialHazardSignal | None:
        sources = [("citizen_description", description or "")]
        sources.extend(("image_evidence", item) for item in visible_evidence)
        for source, text in sources:
            for term in self.potential_hazard_terms:
                match = re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text, flags=re.IGNORECASE)
                if match:
                    return PotentialHazardSignal(source=source, evidence=match.group(0))
        return None

    def assess_priority(self, criteria: list[str] | tuple[str, ...]) -> PriorityAssessment:
        """Map validated evidence criteria to an explainable provisional priority."""
        unique = tuple(dict.fromkeys(criteria))
        unknown = set(unique) - set(self.priority_criteria)
        if unknown:
            raise AnalysisPolicyError(f"Unknown priority criteria: {', '.join(sorted(unknown))}")
        score = sum(int(self.priority_criteria[item]["points"]) for item in unique)
        if score <= self.low_max:
            recommendation = "low"
            band = f"0–{self.low_max}"
        elif score <= self.medium_max:
            recommendation = "medium"
            band = f"{self.low_max + 1}–{self.medium_max}"
        else:
            recommendation = "high"
            band = f"{self.high_min}+"
        explanations = tuple(
            f"{item}: {self.priority_criteria[item]['description']} (+{self.priority_criteria[item]['points']})."
            for item in unique
        )
        explanations += (f"Score {score} maps to {recommendation} under provisional {band}-point bands.",)
        review_required = bool(self.human_review_criteria.intersection(unique))
        return PriorityAssessment(recommendation, score, unique, explanations, review_required)
