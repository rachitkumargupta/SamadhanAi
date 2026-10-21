# Backend (initial citizen intake/tracking slice)

This is a partial implementation, not the target MVP. It currently supports text-only authenticated citizen intake and owner-scoped tracking. The supplied blueprint targets required image intake, GPS/manual location, asynchronous analysis, validated routing, parent/child work, deterministic SLA processing, event-triggered escalation, notification records, staff workflows, and citizen verification; these are not implemented here.

## Provisional choices

- Python 3.13 (workspace runtime observed)
- FastAPI for HTTP
- PostgreSQL through SQLAlchemy 2.x and psycopg
- Alembic for schema migrations
- Externally issued HS256 JWTs for the current citizen routes (anonymous submission/tracking is target project policy but is not implemented in this backend slice)

The starter uses the listed Python stack. The target blueprint recommends PostgreSQL/pgvector, LangGraph, a provider-independent vision/language adapter, private object storage, and a durable scheduled Python worker. These target integrations are not present. The current API verifies tokens but does not issue them or connect to an identity provider. A real issuer must use the configured secret, issuer, audience, and `role=citizen` claim. Do not use placeholder values outside local setup.

## Configuration

Copy the root `.env.example` to `.env` and set a local PostgreSQL URL plus a strong JWT verification secret and the claims used by the approved token issuer. `.env` is ignored by Git. No real secrets are included.

## Local setup status

The requirements have been installed into the workspace's ignored `.venv`. The application has not been started. No PostgreSQL service or issuer configuration was available in the workspace during setup.

## Run locally

1. Create and activate a Python virtual environment.
2. Install the root `requirements.txt`.
3. Start a local PostgreSQL instance and configure `.env`.
4. Apply migrations with `alembic -c backend/alembic.ini upgrade head`.
5. Start the API with `uvicorn backend.app.main:app --reload` from the workspace root.

The user must obtain a valid token from an approved issuer before calling protected routes. There is intentionally no development token endpoint.

## Current API

- `POST /api/v1/complaints` — submit a complaint as an authenticated citizen.
- `GET /api/v1/complaints` — list the caller's complaints (`limit` and `offset`, bounded).
- `GET /api/v1/complaints/{public_reference}` — retrieve the caller's own complaint.
- `GET /api/v1/complaints/{public_reference}/events` — retrieve citizen-visible history only.
- `GET /health/live` — process liveness only.

These routes do not yet implement the image-first or staff workflow specified by the target blueprint. An image is a required input in the target; the current route instead accepts text and optional location and does not accept media.

The submission currently accepts a description and optional location text. Product owners must confirm required fields and location/privacy policy before a pilot. Creation and initial audit event are committed in one database transaction.

Each complaint event stores the request correlation ID when one is available. The API validates or generates this ID and returns it in the `X-Correlation-ID` response header, allowing support staff to relate an audit event to request logs. Existing events remain valid with a null correlation ID.

Application-raised errors, request validation failures, and framework-generated HTTP errors use the shared safe error envelope with a correlation ID. Unknown paths and unsupported methods therefore have the same response shape as other HTTP errors.

The candidate lifecycle state machine is isolated in `backend/app/domain/lifecycle.py`; an internal transition service persists state and its audit event atomically. It does not yet match the blueprint's complete proposed states, parent/child rules, independent SLA state, 48-hour verification/dispute flow, or independent review. It is not wired to an HTTP endpoint and must not be treated as approved policy. See [target lifecycle](../docs/architecture/complaint-lifecycle.md) and [roadmap](../docs/planning/roadmap.md).
