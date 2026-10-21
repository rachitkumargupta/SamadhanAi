# ADR-001: Recommended technology stack

- **Status:** Blueprint-aligned recommendation; Team Kafka approval and deployment validation pending
- **Date:** 2026-10-21
- **Decision owners:** Team Kafka, with backend/AI/frontend/operations input
- **Source:** [Master implementation blueprint](../architecture/implementation-blueprint.md)

## Context

The supplied complete blueprint names a preferred stack and workload: image-first intake, asynchronous work, three constrained agents, PostgreSQL-backed application data/jobs, and deterministic scheduled SLA processing. The existing backend already uses Python, FastAPI, Pydantic, SQLAlchemy, Alembic, PostgreSQL driver, JWT verification, and migrations, but it does not implement the full target. No production provider or deployment has been validated.

## Recommendation

| Area | Target recommendation | Status/qualification |
|---|---|---|
| Backend/API | Python, FastAPI, Pydantic, SQLAlchemy, Alembic | Present in current starter; confirm versions and support. |
| Primary database | PostgreSQL | Target source of truth; deployment/version needs approval. |
| Policy retrieval | pgvector | Recommended for approved, source-linked policy retrieval; not implemented. |
| Agent orchestration | LangGraph and PostgreSQL-backed workflow persistence where appropriate | Recommended; prototype/version/provider selection pending. Exactly three core agents. |
| Model access | Provider-independent vision/language model adapter | Select after hardware/free-tier, quality, privacy, cost, and data-handling evaluation. |
| Background work | Scheduled Python worker and PostgreSQL-backed durable jobs/events | Target requirement for async AI and SLA processing; scheduler and safe job claiming must suit hosting. Database alone is not a scheduler. |
| Media | Private persistent object storage | Provider, scanning, size/dimension limits, retention and access policies pending. |
| Authentication | JWT-based protected staff operations | Identity issuer and role/scope model pending; anonymous citizen tracking needs separate secret/equivalent. |
| Frontend | React with JavaScript | Target recommendation; framework versions pending. |
| API verification | FastAPI OpenAPI; Postman or equivalent | Contract ownership and workflow pending. |
| Source control | Git/GitHub | Project repository exists; team workflow/branch policy pending. |

## Selection principles

Prefer free/open-source tools where practical; avoid recurring costs and unsupported service guarantees. Do not add Redis, Kafka, Celery, microservices, Kubernetes, extra agents, or MCP without a concrete need. External municipal APIs remain optional until authorized access and contracts exist. Free hosting may sleep/restart; recovery must be designed and continuous monitoring must not be promised without a corresponding platform guarantee.

## Consequences and open decisions

This ADR records recommended direction, not blanket approval or proof of integration. Confirm concrete versions, licenses, model/provider and image-data terms, LangGraph persistence, object storage/scanning, scheduler/claim mechanism, deployment, notifications, test/CI tooling, and maintainers before those components enter production. Update the ADR with rationale and evidence as selections are made.
