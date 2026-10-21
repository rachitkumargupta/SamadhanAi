# Complaint Analyst integration contract

**Status:** Implemented first-agent vertical slice: image-first intake, private local storage, durable job execution, and result/status persistence. Production storage/scanning, final taxonomy/priority rules, and provider approval remain open.

## Purpose and boundaries

The Complaint Analyst reads one complaint image and the minimum optional citizen description/location context. It returns a versioned, typed proposal. It has no database session, complaint mutation, routing, assignment, notification, SLA, or lifecycle authority. The application must validate the result and own persistence and any subsequent action.

## Python interface

```python
from backend.app.agents.complaint_analyst import AnalystInput, build_complaint_analyst
from backend.app.config import get_settings

agent = build_complaint_analyst(get_settings())
proposal = agent.analyze(AnalystInput(
    image=image_bytes,
    description="Water is leaking near the sidewalk",
    location_text="Citizen-provided location, if permitted",
))
```

`image` is required. Accepted decoded formats are JPEG, PNG, and WebP. The module caps uploads at 10 MiB and 20 megapixels, applies EXIF orientation, converts to JPEG, and drops source metadata before the provider call. It does not persist uploaded bytes; callers must use private storage and access control.

The `ComplaintAnalysis` schema version is `1.0`. It contains:

- `outcome`: `completed`, `needs_review`, or `insufficient_context`;
- `generated_description`: grounded short description when citizen text is absent;
- `visible_evidence`, `facts`, and `inferences` as separately identified lists;
- nullable `category`, `severity_recommendation`, and `priority_recommendation`;
- `uncertainty`, `missing_information`, and `contradictory_information` lists;
- `possible_multi_department`, `human_review_recommended`, and review reasons.

Recommendation levels are `low`, `medium`, `high`, and `critical`. Their policy meaning is not approved; they must not directly trigger workflow decisions. Categories default to roads/potholes, garbage/sanitation, drainage/sewage, water/leakage, streetlights/electrical, damaged public infrastructure, and other/uncertain. Override the comma-separated `COMPLAINT_ANALYST_CATEGORIES` setting only with approved taxonomy identifiers. Unknown categories are rejected.

The model is instructed to report visible observations separately from inferences, avoid inferring cause/jurisdiction/responsible department, and recommend review for uncertainty or safety concerns. These are model instructions, not deterministic safety or priority policy. Application policy checks and human review remain necessary.

## Provider configuration and errors

The current adapter uses the OpenAI Responses API with Structured Outputs. Configure:

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | API credential; absent/blank means `AnalystUnavailable` |
| `COMPLAINT_ANALYST_MODEL` | Vision-capable model ID; default `gpt-6-luna` |
| `COMPLAINT_ANALYST_TIMEOUT_SECONDS` | Bounded provider timeout; default 30 seconds |
| `COMPLAINT_ANALYST_CATEGORIES` | Comma-separated allowed taxonomy IDs |
| `COMPLAINT_MEDIA_STORAGE_DIR` | Private local normalized-image directory; default `./private_media` |
| `COMPLAINT_ANALYSIS_WORKER_POLL_SECONDS` | Idle worker polling interval; default 2 seconds |

The request sets `store=false` and disables SDK retries. Provider/network/parse failures raise `AnalystProviderError`; invalid or oversized uploads raise `AnalystInputError`. No fallback response is synthesized. A caller should persist the complaint/media/job before invocation as required by the architecture, and record an explicit failure/review outcome if analysis fails.

## Workflow/API integration status

`POST /api/v1/complaints` accepts `multipart/form-data`: required `image`, optional `description`, and optional `location_text`. It returns a complaint reference and queued analysis status. `GET /api/v1/complaints/{public_reference}/analysis` is owner-scoped and returns `pending`, `running`, `succeeded`, or `failed`; successful responses include the run ID and typed result. Terminal failure responses do not disclose provider details.

Example request:

```sh
curl -X POST http://localhost:8000/api/v1/complaints \
  -H "Authorization: Bearer $CITIZEN_TOKEN" \
  -F "image=@pothole.jpg" \
  -F "description=Large pothole near the crossing" \
  -F "location_text=Ward 4"
```

The initial response includes `public_reference`, `analysis_status: "pending"`, and the complaint fields. Polling the owner-scoped status endpoint returns the durable job status and, after success, the versioned `result` plus `run_id`.

Before any model call, the API normalizes and privately stores the image, then commits the complaint, media reference, initial event, and unique durable job in one transaction. The separate worker claims jobs with a PostgreSQL row lock and lease, creates an `agent_runs` record per attempt, and stores successful results in `complaint_analysis`. Provider failures receive bounded retries; exhausted/misconfigured jobs become a manual-review state without changing complaint status. Run it with `python -m backend.app.workers.complaint_analysis_worker`; `--once` processes at most one job. Do not expose local file paths or raw provider errors to citizens.

Job execution is at-least-once. A worker crash after the provider responds but before the result transaction commits can cause a repeated provider call after lease expiry. Persisted output is associated with a unique run/attempt and no complaint action is applied by the worker. A staffed review queue and operator retry screen are not implemented; terminal failures are currently visible through the status record and operational database access.

The current private local filesystem adapter is for development/single-host use only. Only the normalized image is retained; original-evidence retention, malware scanning, production object storage, retention/deletion and access operations need policy/security approval. The OpenAI adapter is implemented for development but remains subject to project approval of the provider, model, and data-handling terms. Deterministic category/priority/safety policy is not implemented because the project taxonomy and thresholds are still unapproved; model recommendations must not be used as operational authority.

## Tests

Install test dependencies with `pip install -r requirements-dev.txt`, then run `python -m unittest discover -s tests -v`. Tests use deterministic provider stubs and do not require credentials or make network calls. Live provider behavior requires an approved/configured API key and has not been exercised with citizen data.
