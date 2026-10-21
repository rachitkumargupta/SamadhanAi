# Complaint Analyst integration contract

**Status:** Image-first workflow and a configurable provisional analysis framework are implemented. The framework is not municipal policy; production media controls, provider approval, and official approval of taxonomy and priority values remain open. See the [MVP analysis framework](complaint-analysis-mvp-policy.md).

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

The provider proposal and enriched `ComplaintAnalysis` schema version is `1.1`. It contains:

- `outcome`: `completed`, `needs_review`, or `insufficient_context`;
- `generated_description`: grounded short description when citizen text is absent;
- `visible_evidence`, `facts`, and `inferences` as separately identified lists;
- nullable `category`, `severity_recommendation`, and `priority_recommendation`;
- model `confidence_level` (`high`, `medium`, `low`), explicitly not a calibrated probability;
- evidence-linked `priority_factors`, with policy-computed score, criteria, explanation, and separate retained model priority suggestion;
- `uncertainty`, `missing_information` with stable codes, and `contradictory_information` lists;
- `possible_multi_department`, `human_review_recommended`, and review reasons.

The configured policy and its explicit provisional priority criteria are documented in the [MVP analysis framework](complaint-analysis-mvp-policy.md) and stored in `backend/app/agents/analysis_policy.json`. The seven category IDs are the candidates listed in FR-ANL-06. They are configurable defaults, not approved municipal taxonomy. `COMPLAINT_ANALYST_CATEGORIES` can restrict (not expand) the policy taxonomy and must include its uncertain fallback; use `COMPLAINT_ANALYST_POLICY_FILE` to select a revised policy JSON. Invalid model categories are converted to `other_uncertain` and flagged for review. Computed priorities are low/medium/high; critical is never assigned automatically. The model's original priority suggestion remains separately visible. None of the provisional values may trigger workflow decisions.

The model is instructed to report visible observations separately from inferences, avoid inferring cause/jurisdiction/responsible department, give a categorical confidence self-assessment, and cite priority factors to image evidence or citizen text. Application code validates factor references, applies the deterministic configured score, flags missing location, and forces review for medium/low confidence, conflict, insufficient visual evidence, unsupported factors, fallback classification, or potential hazard. These are provisional engineering rules, not official municipal or emergency policy; human review remains necessary.

## Provider configuration and errors

The current adapter uses the OpenAI Responses API with Structured Outputs. Configure:

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | API credential; absent/blank means `AnalystUnavailable` |
| `COMPLAINT_ANALYST_MODEL` | Vision-capable model ID; default `gpt-6-luna` |
| `COMPLAINT_ANALYST_TIMEOUT_SECONDS` | Bounded provider timeout; default 30 seconds |
| `COMPLAINT_ANALYST_CATEGORIES` | Comma-separated allowed taxonomy IDs |
| `COMPLAINT_ANALYST_POLICY_FILE` | Optional path to a versioned policy JSON replacing the bundled provisional MVP policy |
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

Job execution is at-least-once. A worker crash after the provider responds but before the result transaction commits can cause a repeated provider call after lease expiry. Persisted output is associated with a unique run/attempt and no complaint action is applied by the worker. `GET /api/v1/staff/complaint-analysis/reviews` now lists failed analyses and results that require human review; the linked image route returns the normalized JPEG with private no-store caching. Both require a signed JWT containing the explicit `complaint_analysis:review` permission. The trusted identity provider must grant this only to approved staff. The current queue is read-only: assignment, disposition/override recording, scoped reviewer eligibility, and operator retry are still unimplemented because review ownership and staff authorization decisions remain open.

The current private local filesystem adapter is for development/single-host use only. Only the normalized image is retained; original-evidence retention, malware scanning, production object storage, retention/deletion and access operations need policy/security approval. The OpenAI adapter is implemented for development but remains subject to project approval of the provider, model, and data-handling terms. A configurable deterministic MVP taxonomy/priority framework now exists; it is explicitly provisional pending policy approval. It provides explainable priority proposals and conservative review triggers, not official priority thresholds or emergency decisions. Model recommendations must not be used as operational authority.

## Tests

Install test dependencies with `pip install -r requirements-dev.txt`, then run `python -m unittest discover -s tests -v`. Tests use deterministic provider stubs and do not require credentials or make network calls. Live provider behavior requires an approved/configured API key and has not been exercised with citizen data.

## Quality evaluation

`python -m backend.app.evaluation.complaint_analyst <manifest.jsonl> --allow-provider-processing` runs an evaluation set through the configured provider. The explicit flag is required because each image and its supplied context are sent to that provider. Use only images and labels approved for this purpose; do not place real citizen evidence in the repository. The runner emits per-case success/failure and exact-match accuracy for whichever expected category, priority, severity, and review labels are supplied, plus review precision/recall when review labels are present. It does not print complaint content or provider error text, score free-text grounding, or decide pass/fail.

Each non-comment JSONL line has an `id`, an image path relative to the manifest, optional `description` and `location_text`, and at least one expected label:

```json
{"id":"approved-case-001","image":"images/001.jpg","description":"","expected":{"category":"roads_potholes","human_review_recommended":true}}
```

There is no approved, representative labeled set or acceptance threshold yet. The policy/data owner must approve the dataset, labeling rubric, provider use, and quality thresholds before results can be treated as a release decision. Generated descriptions and evidence grounding still require human rubric-based review.
