# ADR-002: Initial application architecture

- **Status:** Proposed; pending Team Kafka approval
- **Date:** 2026-10-16
- **Decision owners:** Team Kafka, with backend and integration workstream input

## Context

The supplied complete blueprint defines eight logical layers, exactly three agents, image-first intake, asynchronous analysis, parent/child departmental tickets, and deterministic scheduled SLA processing. An initial backend slice exists, so implementation must extend and preserve it rather than assume an empty repository. The deployment platform and workload limits still require validation.

## Proposal

Use a modular monolith: FastAPI API/security, application/domain services, PostgreSQL persistence, the shared harness for exactly three agents, provider adapters, and a scheduled worker for durable jobs/SLA processing. Persist complaint/media references/events and durable analysis work before model calls. Parent-child tickets have independent assignments, state, evidence, and SLA. Keep agent calls/external effects behind interfaces; enforce authorization, state, deadlines and writes in application/domain code. Do not split into separate services without measured need.

## Alternatives considered

- **Separate service per layer/agent:** adds deployment and operational coordination without demonstrated MVP need.
- **Direct AI-to-database/tool access:** rejected because it bypasses application authorization, invariants, and audit boundaries.
- **Single unstructured API module:** simpler initially but weakens separation of domain rules, persistence, and integrations as workstreams grow.

## Consequences

One application simplifies local development and lifecycle transactions. The worker must share application rules while recovering durable work after restarts; a database is not a scheduler, so job claiming and hosting guarantees need an explicit choice. This ADR does not select a cloud platform, model provider, object-storage provider, or concrete scheduler.
