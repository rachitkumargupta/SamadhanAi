# Backend (citizen intake/tracking and Complaint Analyst core)

This is a partial implementation, not the target MVP. It supports authenticated image-first complaint intake, private local media persistence, durable asynchronous Complaint Analyst jobs/results, owner-scoped tracking, a capability-protected read-only Analyst review queue with image access, and a configurable provisional taxonomy/priority framework. Municipal approval of the taxonomy/rubric, production object storage and scanning, review assignment/dispositions/retries, routing, parent/child work, SLA processing, escalation, notifications, broader staff workflows, and citizen verification remain open.

## Provisional choices

- Python 3.13 (workspace runtime observed)
- FastAPI for HTTP
- PostgreSQL through SQLAlchemy 2.x and psycopg
- Alembic for schema migrations
- Externally issued HS256 JWTs for the current citizen routes (anonymous submission/tracking is target project policy but is not implemented in this backend slice)

The current API verifies tokens but does not issue them or connect to an identity provider. A real issuer must use the configured secret, issuer, audience, and `role=citizen` claim. Do not use placeholder values outside local setup. The Complaint Analyst worker is a durable database-backed Python process; PostgreSQL is required for safe multi-worker job claiming. The local filesystem store is a development adapter and is not an approved production object-storage solution.

## Configuration

Copy the root `.env.example` to `.env` and set a local PostgreSQL URL plus a strong JWT verification secret and the claims used by the approved token issuer. `.env` is ignored by Git. No real secrets are included.

## Local setup status

The requirements have been installed into the workspace's ignored `.venv`. The application has not been started. No PostgreSQL service or issuer configuration was available in the workspace during setup.

## Run locally

1. Create and activate a Python virtual environment.
2. Install the root `requirements.txt`; use `requirements-dev.txt` when running the tests.
3. Start a local PostgreSQL instance and configure `.env`.
4. Apply migrations with `alembic -c backend/alembic.ini upgrade head`.
5. Start the API with `uvicorn backend.app.main:app --reload` from the workspace root.
6. In a separate process, start the Analyst worker with `python -m backend.app.workers.complaint_analysis_worker`.

The user must obtain a valid token from an approved issuer before calling protected routes. There is intentionally no development token endpoint.

## Current API

- `POST /api/v1/complaints` — submit a complaint as an authenticated citizen.
- `GET /api/v1/complaints/{public_reference}/analysis` — retrieve the caller's analysis job status and, when complete, its typed proposal.
- `GET /api/v1/complaints` — list the caller's complaints (`limit` and `offset`, bounded).
- `GET /api/v1/complaints/{public_reference}` — retrieve the caller's own complaint.
- `GET /api/v1/complaints/{public_reference}/events` — retrieve citizen-visible history only.
- `GET /health/live` — process liveness only.

Complaint creation uses multipart form data. `image` is required; `description` (up to 5,000 characters) and `location_text` (up to 500 characters) are optional. The image is decoded, limited to 10 MiB and 20 megapixels, EXIF-oriented, normalized to JPEG, and stored outside the web root under an opaque key. Only the normalized copy is currently retained. The storage/evidence policy, malware scanning, retention and production object store still require approval before real-citizen use.

Complaint, media reference, initial audit event, and analysis job are committed in one database transaction before the provider is called. The worker records an `agent_runs` row for each attempt and stores successful proposals in `complaint_analysis`; failures use bounded retries and a terminal failed status with a review-required marker. The staff read-only review queue lists human-review results and failed jobs, and its image endpoint returns only normalized evidence with private no-store caching. Both require a signed token carrying `complaint_analysis:review`; the trusted issuer must grant this only to approved staff. Assignment, review disposition, scoped eligibility, and operator retry are not implemented. The worker never changes complaint status or makes routing decisions.

Each complaint event stores the request correlation ID when one is available. The API validates or generates this ID and returns it in the `X-Correlation-ID` response header, allowing support staff to relate an audit event to request logs. Existing events remain valid with a null correlation ID.

Application-raised errors, request validation failures, and framework-generated HTTP errors use the shared safe error envelope with a correlation ID. Unknown paths and unsupported methods therefore have the same response shape as other HTTP errors.

The candidate lifecycle state machine is isolated in `backend/app/domain/lifecycle.py`; an internal transition service persists state and its audit event atomically. It does not yet match the blueprint's complete proposed states, parent/child rules, independent SLA state, 48-hour verification/dispute flow, or independent review. It is not wired to an HTTP endpoint and must not be treated as approved policy. See [target lifecycle](../docs/architecture/complaint-lifecycle.md) and [roadmap](../docs/planning/roadmap.md).

## Complaint Analyst workflow

`POST /api/v1/complaints` returns the complaint reference and `analysis_status: pending`. Use `GET /api/v1/complaints/{public_reference}/analysis` to poll the job; a successful result includes the versioned proposal and run ID. A terminal failure returns a generic manual-review message without exposing provider details.

The callable core in `backend/app/agents/complaint_analyst.py` returns a typed proposal with visible evidence, facts/inferences, category and severity/priority recommendations, uncertainty, missing/contradictory information, multi-department possibility, and human-review recommendation. Taxonomy and deterministic priority scoring are configurable in the versioned provisional policy. Its criteria and thresholds are engineering defaults, not approved municipal policy; recommendations must not trigger workflow actions.

Configure `OPENAI_API_KEY`, `COMPLAINT_ANALYST_MODEL`, `COMPLAINT_ANALYST_TIMEOUT_SECONDS`, optional `COMPLAINT_ANALYST_POLICY_FILE` / `COMPLAINT_ANALYST_CATEGORIES`, `COMPLAINT_MEDIA_STORAGE_DIR`, and `COMPLAINT_ANALYSIS_WORKER_POLL_SECONDS`. The default versioned policy lives at `backend/app/agents/analysis_policy.json` and is explicitly a provisional engineering baseline, not municipal policy. The OpenAI adapter is the current development adapter; the project has not approved a production provider, model, or data-handling agreement. Missing credentials fail the job into manual review; results are never fabricated. See the [MVP analysis framework](../docs/architecture/complaint-analysis-mvp-policy.md) and [integration contract](../docs/architecture/complaint-analyst-integration.md).

Run tests after installing `requirements-dev.txt` with `python -m unittest discover -s tests -v`.
