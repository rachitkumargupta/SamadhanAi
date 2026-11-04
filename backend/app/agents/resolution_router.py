"""Resolution and Routing Agent (Agent 2).

Determines:
- Responsible municipal department from Agent 1 validated category
- Responsible ward / jurisdiction from verified GPS coordinates
- Deterministically selected eligible officer based on workload and permissions
- Deterministic SLA duration and deadline calculation
- Safe routing decision or human-review triage

This module adheres to strict architectural rules:
1. Pure business logic - never re-classifies images or re-analyzes complaints.
2. Deterministic execution - never uses an LLM to select officers or invent SLAs.
3. Safe defaults - any missing, invalid, or uncertain input routes to manual review.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Sequence
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.app.models import Department, Officer, SLAPolicy, Ward


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RoutingInput(BaseModel):
    """Normalized input from persisted Agent 1 output and complaint context."""

    model_config = ConfigDict(extra="forbid")

    complaint_id: UUID
    category: str
    priority: str
    confidence_level: str = "medium"
    human_review_recommended: bool = False
    location_text: str | None = None
    analysis_outcome: str = "completed"


class RoutingProposal(BaseModel):
    """Deterministic routing decision proposal produced by Agent 2."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    complaint_id: UUID
    category: str
    priority: str
    status: str  # "assigned", "needs_review", "unassigned"
    department_id: UUID | None = None
    department_code: str | None = None
    ward_id: UUID | None = None
    ward_code: str | None = None
    assigned_officer_id: UUID | None = None
    officer_name: str | None = None
    sla_hours: int | None = None
    sla_deadline: datetime | None = None
    routing_reason: str
    requires_human_review: bool = False


class RoutingPolicy:
    """Configurable routing policy loaded from versioned JSON."""

    def __init__(
        self,
        *,
        policy_id: str,
        version: str,
        approval_status: str,
        notice: str,
        category_department_mapping: dict[str, str],
        default_sla_hours: dict[str, int],
        default_fallback_sla_hours: int,
        required_officer_permission: str,
    ):
        self.policy_id = policy_id
        self.version = version
        self.approval_status = approval_status
        self.notice = notice
        self.category_department_mapping = category_department_mapping
        self.default_sla_hours = default_sla_hours
        self.default_fallback_sla_hours = default_fallback_sla_hours
        self.required_officer_permission = required_officer_permission

    @classmethod
    def load(cls, path: str | Path | None = None) -> RoutingPolicy:
        policy_path = Path(path) if path else Path(__file__).with_name("routing_policy.json")
        try:
            raw = json.loads(policy_path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise ValueError(f"Cannot load Routing policy file: {policy_path}") from exc

        return cls(
            policy_id=raw.get("policy_id", "samadhan_resolution_routing_mvp"),
            version=raw.get("version", "1.0-provisional"),
            approval_status=raw.get("approval_status", "provisional_engineering_default_not_municipal_policy"),
            notice=raw.get("notice", "Demo configuration only"),
            category_department_mapping=dict(raw.get("category_department_mapping", {})),
            default_sla_hours={k.lower(): int(v) for k, v in raw.get("default_sla_hours", {}).items()},
            default_fallback_sla_hours=int(raw.get("default_fallback_sla_hours", 48)),
            required_officer_permission=str(raw.get("required_officer_permission", "complaint:resolve")),
        )


def parse_coordinates(location_text: str | None) -> tuple[float, float] | None:
    """Extract and validate (latitude, longitude) from freeform or formatted location text.

    Supported patterns:
    - "12.9716, 77.5946" or "12.9716,77.5946"
    - "lat: 12.9716, lon: 77.5946" / "lat: 12.9716, lng: 77.5946"
    - "POINT(77.5946 12.9716)" (WKT lon-lat)
    - JSON {"lat": 12.9716, "lon": 77.5946}
    """
    if not location_text or not location_text.strip():
        return None

    text = location_text.strip()

    # Try JSON
    if text.startswith("{") and text.endswith("}"):
        try:
            data = json.loads(text)
            lat = data.get("lat") or data.get("latitude")
            lon = data.get("lon") or data.get("lng") or data.get("longitude")
            if lat is not None and lon is not None:
                lat_f, lon_f = float(lat), float(lon)
                if _is_valid_coordinate(lat_f, lon_f):
                    return (lat_f, lon_f)
        except (json.JSONDecodeError, ValueError, TypeError):
            pass

    # Try WKT: POINT(lon lat)
    wkt_match = re.search(r"POINT\s*\(\s*([+-]?\d+(?:\.\d+)?)\s+([+-]?\d+(?:\.\d+)?)\s*\)", text, re.IGNORECASE)
    if wkt_match:
        try:
            lon_f = float(wkt_match.group(1))
            lat_f = float(wkt_match.group(2))
            if _is_valid_coordinate(lat_f, lon_f):
                return (lat_f, lon_f)
        except ValueError:
            pass

    # Try labeled: lat: ..., lon: ...
    labeled_match = re.search(
        r"lat(?:itude)?\s*[:=]\s*([+-]?\d+(?:\.\d+)?)\s*[,; ]+\s*(?:lon(?:gitude)?|lng)\s*[:=]\s*([+-]?\d+(?:\.\d+)?)",
        text,
        re.IGNORECASE,
    )
    if labeled_match:
        try:
            lat_f = float(labeled_match.group(1))
            lon_f = float(labeled_match.group(2))
            if _is_valid_coordinate(lat_f, lon_f):
                return (lat_f, lon_f)
        except ValueError:
            pass

    # Try standard "lat, lon"
    comma_match = re.search(r"([+-]?\d+(?:\.\d+)?)\s*,\s*([+-]?\d+(?:\.\d+)?)", text)
    if comma_match:
        try:
            lat_f = float(comma_match.group(1))
            lon_f = float(comma_match.group(2))
            if _is_valid_coordinate(lat_f, lon_f):
                return (lat_f, lon_f)
        except ValueError:
            pass

    return None


def _is_valid_coordinate(lat: float, lon: float) -> bool:
    """Validate latitude [-90, 90] and longitude [-180, 180]."""
    import math

    if math.isnan(lat) or math.isnan(lon) or math.isinf(lat) or math.isinf(lon):
        return False
    return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0


def find_ward(lat: float, lon: float, active_wards: Sequence[Ward]) -> Ward | None:
    """Locate responsible ward using bounding box matching."""
    for ward in active_wards:
        if not ward.is_active:
            continue
        if ward.min_lat <= lat <= ward.max_lat and ward.min_lon <= lon <= ward.max_lon:
            return ward
    return None


def select_eligible_officer(
    department_id: UUID,
    ward_id: UUID,
    active_officers: Sequence[Officer],
    required_permission: str,
) -> Officer | None:
    """Select the best eligible officer deterministically.

    Rules:
    - Active status == True
    - Assigned to target department
    - Assigned to target ward
    - Holds required permission
    - Workload optimization: least active complaints count
    - Deterministic tie-breaker: officer ID
    """
    eligible: list[Officer] = []
    for officer in active_officers:
        if not officer.is_active:
            continue
        if officer.department_id != department_id:
            continue
        if officer.ward_id != ward_id:
            continue
        permissions = officer.permissions or []
        if required_permission not in permissions:
            continue
        eligible.append(officer)

    if not eligible:
        return None

    # Deterministic sort: ascending active workload, then stable ID string tie-break
    eligible.sort(key=lambda off: (off.active_complaints_count, str(off.id)))
    return eligible[0]


def calculate_sla(
    category: str,
    priority: str,
    assigned_at: datetime,
    active_sla_policies: Sequence[SLAPolicy],
    policy: RoutingPolicy,
) -> tuple[int, datetime]:
    """Calculate deterministic SLA deadline based on category, priority, and policies."""
    norm_cat = category.strip().lower()
    norm_pri = priority.strip().lower()

    # 1. Match database policy
    for sla_rule in active_sla_policies:
        if not sla_rule.is_active:
            continue
        if sla_rule.category.lower() == norm_cat and sla_rule.priority.lower() == norm_pri:
            duration = sla_rule.duration_hours
            return duration, assigned_at + timedelta(hours=duration)

    # 2. Match default priority SLA from policy configuration
    if norm_pri in policy.default_sla_hours:
        duration = policy.default_sla_hours[norm_pri]
        return duration, assigned_at + timedelta(hours=duration)

    # 3. Fallback default
    duration = policy.default_fallback_sla_hours
    return duration, assigned_at + timedelta(hours=duration)


class ResolutionRouter:
    """Resolution and Routing Agent engine."""

    def __init__(self, policy: RoutingPolicy | None = None):
        self._policy = policy or RoutingPolicy.load()

    def route(
        self,
        routing_input: RoutingInput,
        *,
        departments: Sequence[Department],
        wards: Sequence[Ward],
        officers: Sequence[Officer],
        sla_policies: Sequence[SLAPolicy],
        current_time: datetime | None = None,
    ) -> RoutingProposal:
        now = current_time or utc_now()
        complaint_id = routing_input.complaint_id
        category = routing_input.category
        priority = routing_input.priority

        # 1. Check if Agent 1 flagged human review or had non-completed outcome
        if routing_input.human_review_recommended or routing_input.analysis_outcome != "completed":
            return RoutingProposal(
                complaint_id=complaint_id,
                category=category,
                priority=priority,
                status="needs_review",
                routing_reason="Complaint flagged for human review by Agent 1 triage.",
                requires_human_review=True,
            )

        # 2. Check department mapping for category
        dept_code = self._policy.category_department_mapping.get(category)
        if not dept_code:
            return RoutingProposal(
                complaint_id=complaint_id,
                category=category,
                priority=priority,
                status="needs_review",
                routing_reason=f"Category '{category}' has no configured department mapping; manual triage required.",
                requires_human_review=True,
            )

        # Look up Department in DB
        department = next((d for d in departments if d.code == dept_code and d.is_active), None)
        if not department:
            return RoutingProposal(
                complaint_id=complaint_id,
                category=category,
                priority=priority,
                status="needs_review",
                routing_reason=f"Responsible department code '{dept_code}' is not active or registered in the database.",
                requires_human_review=True,
            )

        # 3. Detect Ward / Jurisdiction via GPS
        coords = parse_coordinates(routing_input.location_text)
        if coords is None:
            return RoutingProposal(
                complaint_id=complaint_id,
                category=category,
                priority=priority,
                department_id=department.id,
                department_code=department.code,
                status="needs_review",
                routing_reason="Missing or invalid GPS coordinates; cannot reliably detect municipal ward.",
                requires_human_review=True,
            )

        lat, lon = coords
        ward = find_ward(lat, lon, wards)
        if not ward:
            return RoutingProposal(
                complaint_id=complaint_id,
                category=category,
                priority=priority,
                department_id=department.id,
                department_code=department.code,
                status="needs_review",
                routing_reason=f"Coordinates ({lat:.5f}, {lon:.5f}) fall outside all active municipal ward boundaries.",
                requires_human_review=True,
            )

        # 4. Calculate SLA
        sla_hours, sla_deadline = calculate_sla(category, priority, now, sla_policies, self._policy)

        # 5. Select eligible Officer
        eligible_officer = select_eligible_officer(
            department_id=department.id,
            ward_id=ward.id,
            active_officers=officers,
            required_permission=self._policy.required_officer_permission,
        )

        if not eligible_officer:
            return RoutingProposal(
                complaint_id=complaint_id,
                category=category,
                priority=priority,
                department_id=department.id,
                department_code=department.code,
                ward_id=ward.id,
                ward_code=ward.code,
                sla_hours=sla_hours,
                sla_deadline=sla_deadline,
                status="unassigned",
                routing_reason=f"No active officer with permission '{self._policy.required_officer_permission}' found in ward '{ward.name}' for department '{department.name}'. Queued for supervisor assignment.",
                requires_human_review=True,
            )

        # 6. Complete successful assignment proposal
        return RoutingProposal(
            complaint_id=complaint_id,
            category=category,
            priority=priority,
            department_id=department.id,
            department_code=department.code,
            ward_id=ward.id,
            ward_code=ward.code,
            assigned_officer_id=eligible_officer.id,
            officer_name=eligible_officer.name,
            sla_hours=sla_hours,
            sla_deadline=sla_deadline,
            status="assigned",
            routing_reason=f"Assigned to officer {eligible_officer.name} ({department.name}, {ward.name}) with {sla_hours}h SLA.",
            requires_human_review=False,
        )
