# Agent 2 — Resolution & Routing Agent

**Status:** Implemented (MVP)  
**Contract Version:** `1.0-provisional`  
**Related:** [AI Agent Architecture](ai-agent-architecture.md), [Complaint Lifecycle](complaint-lifecycle.md)

---

## 1. Purpose and Architecture Boundaries

The **Resolution & Routing Agent (Agent 2)** receives the validated complaint analysis proposal from Agent 1 (Complaint Analyst) and deterministically decides:
1. **Responsible Municipal Department**: Mapped from the validated complaint category.
2. **Responsible Ward / Jurisdiction**: Detected from verified GPS coordinates and municipal boundary definitions.
3. **Eligible Officer Selection**: Assigned based on active status, matching department, jurisdiction, required permissions, and workload balancing.
4. **SLA Assignment**: Calculated via deterministic backend business logic.
5. **Handoff to Agent 3**: Schedules a durable monitoring job for the Escalation & Monitoring Agent.

### Strict Architectural Invariants
- **No LLM in Officer or SLA Selection**: Agent 2 does not use non-deterministic language models for officer dispatch or SLA generation.
- **No Re-Analysis**: Agent 2 never re-reads image attachments or overrides Agent 1 classification.
- **Fail-Safe Human Review**: If GPS coordinates are missing/invalid, coordinates fall outside municipal bounds, categories are unmapped, or Agent 1 recommended human review, Agent 2 flags the complaint for manual supervisor triage rather than guessing.
- **Idempotency**: Retrying routing for the same complaint reference is strictly idempotent; duplicate database assignments and duplicate monitoring jobs are prevented.

---

## 2. Input from Agent 1 (Complaint Analyst)

Agent 2 reads the persisted analysis result from the `complaint_analysis` table and the complaint record:

| Field | Source | Description |
|---|---|---|
| `complaint_id` | `complaints.id` | Unique UUID of the complaint |
| `category` | `complaint_analysis.result['category']` | Detected category (e.g. `roads_potholes`, `garbage_sanitation`) |
| `priority_recommendation` | `complaint_analysis.result['priority_recommendation']` | Priority tier (`low`, `medium`, `high`, `critical`) |
| `confidence_level` | `complaint_analysis.result['confidence_level']` | Model self-assessed confidence |
| `human_review_recommended` | `complaint_analysis.result['human_review_recommended']` | Whether Agent 1 flagged uncertain or hazard context |
| `outcome` | `complaint_analysis.result['outcome']` | Analysis outcome (`completed`, `needs_review`, `insufficient_context`) |
| `location_text` | `complaints.location_text` | Location description or GPS coordinates |

> [!IMPORTANT]
> If `human_review_recommended` is `true` or `outcome != "completed"`, Agent 2 will **never** automatically assign the complaint to an officer. It transitions the ticket to `needs_review` for human verification.

---

## 3. Department Mapping

Configured in `backend/app/agents/routing_policy.json`:

| Complaint Category | Department Code | Responsible Department |
|---|---|---|
| `roads_potholes` | `PWD` | Public Works Department |
| `garbage_sanitation` | `SANITATION` | Sanitation Department |
| `water_leakage` | `WATER_SUPPLY` | Water Supply Department |
| `streetlights_electrical` | `ELECTRICITY` | Electricity Department |
| `drainage_sewage` | `DRAINAGE` | Drainage Department |
| `damaged_public_infrastructure` | `PWD` | Public Works Department |
| `other_uncertain` | *None* | Routes to Manual Review Queue |

> [!NOTE]
> Mappings are fully configurable via JSON policy and database records rather than hardcoded rules.

---

## 4. Jurisdiction & Ward Detection

The router parses GPS coordinates from `complaint.location_text` supporting standard formats:
- Plain coordinates: `"12.9716, 77.5946"`
- Labeled coordinates: `"lat: 12.9716, lon: 77.5946"`
- WKT Geometry: `"POINT(77.5946 12.9716)"`
- JSON payload: `{"latitude": 12.9716, "longitude": 77.5946}`

### Validation Rules:
- Latitude must be between \(-90.0\) and \(+90.0\).
- Longitude must be between \(-180.0\) and \(+180.0\).
- If GPS coordinates are missing or invalid, the complaint status is set to `needs_review` with reason `Missing or invalid GPS coordinates`.
- If coordinates fall outside all active wards in the `wards` table, the complaint status is set to `needs_review` with reason `Coordinates fall outside all active municipal ward boundaries`.

---

## 5. Officer Selection

Eligible officers are selected deterministically using the following rules:
1. `is_active == True`
2. `department_id == matched_department.id`
3. `ward_id == matched_ward.id`
4. `required_officer_permission in permissions` (default: `"complaint:resolve"`)
5. **Workload balancing**: If multiple officers qualify, the officer with the lowest `active_complaints_count` is selected.
6. **Tie-breaking**: Deterministic secondary sort on the officer's UUID ensures reproducible assignment.

If no officer meets these criteria, the complaint assignment is marked as `unassigned` and queued for supervisor dispatch.

---

## 6. Deterministic SLA Calculation

SLA duration is calculated in business logic:
$$\text{deadline} = \text{assigned\_at} + \Delta t_{\text{hours}}$$

### Policy Lookup Priority:
1. Exact match in `sla_policies` table for `(category, priority)`.
2. Fallback to `default_sla_hours` in `routing_policy.json`:
   - `critical`: 12 hours
   - `high`: 24 hours
   - `medium`: 48 hours
   - `low`: 72 hours
3. Global default fallback: 48 hours.

> [!WARNING]
> Demo SLA values are provisional development defaults and do not represent legally enacted municipal citizen charters or government service standards.

---

## 7. Database Persistence & Lifecycle

The routing outcome is committed in a single atomic database transaction:
- An entry is persisted in `complaint_assignments`.
- `Complaint.status` is updated to `assigned` (or `under_review` if unassigned/review required).
- A audit event is recorded in `complaint_events` (`complaint_assigned`, `routing_review_required`, or `routing_officer_unavailable`).
- If an officer is assigned, `officer.active_complaints_count` is incremented.

---

## 8. Agent 3 (Monitoring & Escalation) Handoff

Upon successful assignment to an eligible officer:
1. A durable `BackgroundJob` is enqueued with:
   - `work_type = "sla_monitoring"`
   - `complaint_id = complaint.id`
   - `idempotency_key = "sla_monitoring:{complaint_id}"`
   - `status = "pending"`
2. Agent 3 is triggered by breach events or monitors tickets approaching their deterministic SLA deadline.
3. The unique `idempotency_key` ensures duplicate monitoring jobs are never created.

---

## 9. API Endpoints

Staff routing endpoints require a valid staff JWT with the `complaint_routing:assign` permission (or `supervisor` role).

### `POST /api/v1/staff/complaint-routing/{public_reference}`
Triggers routing for an analyzed complaint.

**Sample Response (`200 OK`):**
```json
{
  "id": "e6a0c4f1-8b22-48df-9e66-1c20e54be601",
  "complaint_reference": "SAM-D4H7K9M2P1Q8",
  "department_name": "Public Works Department",
  "department_code": "PWD",
  "ward_name": "Central Ward",
  "ward_code": "WARD-01",
  "assigned_officer_id": "73c6a4e2-41f2-4bc3-95b3-3a1bcde41209",
  "officer_name": "Ramesh Sharma",
  "category": "roads_potholes",
  "priority": "medium",
  "status": "assigned",
  "sla_hours": 48,
  "sla_deadline": "2026-11-06T14:30:00Z",
  "routing_reason": "Assigned to officer Ramesh Sharma (Public Works Department, Central Ward) with 48h SLA.",
  "assigned_at": "2026-11-04T14:30:00Z"
}
```

### `GET /api/v1/staff/complaint-routing/{public_reference}`
Retrieves the current assignment and routing details for a complaint.

---

## 10. How to Run Tests

Run all Agent 2 tests with pytest:
```bash
pytest tests/test_resolution_routing.py -v
```

Run the entire test suite:
```bash
pytest tests/
```

---

## 11. Known Limitations & Future Work
- **GIS Geometry**: MVP uses rectangular bounding box checks (`min_lat`, `max_lat`, `min_lon`, `max_lon`). Production deployments should integrate PostGIS polygon boundaries.
- **Dynamic Shift Calendars**: Officer availability currently relies on `is_active` and `active_complaints_count`. Real-world deployments may include leave management and working-hour schedules.
