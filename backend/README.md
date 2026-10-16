# Backend (first vertical slice)

This backend currently covers citizen complaint intake and owner-scoped tracking. It is a first implementation slice, not the complete MVP. Staff roles, classification, routing, assignment, SLA monitoring, notifications, attachments, and AI are not implemented.

## Provisional choices

- Python 3.13 (workspace runtime observed)
- FastAPI for HTTP
- PostgreSQL through SQLAlchemy 2.x and psycopg
- Alembic for schema migrations
- Externally issued HS256 JWTs for citizen authentication

These choices follow the proposed stack and should be confirmed by Team Kafka. The API verifies tokens but does not issue them or connect to an identity provider. A real issuer must use the configured secret, issuer, audience, and `role=citizen` claim. Do not use placeholder values outside local setup.

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

The submission currently accepts a description and optional location text. Product owners must confirm required fields and location/privacy policy before a pilot. Creation and initial audit event are committed in one database transaction.

The candidate lifecycle state machine is isolated in `backend/app/domain/lifecycle.py`; an internal transition service persists state and its audit event atomically. Neither is wired to an HTTP endpoint. Their role names and rules mirror the draft lifecycle document and require team approval before use. Assignment ownership, jurisdiction, and verification policy checks are not implemented by this module.
