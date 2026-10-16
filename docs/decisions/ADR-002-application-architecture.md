# ADR-002: Initial application architecture

- **Status:** Proposed; pending Team Kafka approval
- **Date:** 2026-10-16
- **Decision owners:** Team Kafka, with backend and integration workstream input

## Context

The target architecture describes eight logical layers and three agents. MVP scope requires an understandable, auditable end-to-end lifecycle. There is no existing code or deployment topology to extend, and current workload/integration requirements are unknown.

## Proposal

Begin with a modular monolith: one backend deployment containing API/security, application/domain services, persistence, AI orchestration/harness interfaces, and provider adapters. Use a transactional relational database if approved. Keep agent calls and external side effects behind interfaces; enforce authorization and lifecycle rules in application/domain code. Introduce background execution or separate services only when measured reliability, scaling, isolation, or team ownership requirements justify them.

## Alternatives considered

- **Separate service per layer/agent:** adds deployment and operational coordination without demonstrated MVP need.
- **Direct AI-to-database/tool access:** rejected because it bypasses application authorization, invariants, and audit boundaries.
- **Single unstructured API module:** simpler initially but weakens separation of domain rules, persistence, and integrations as workstreams grow.

## Consequences

One deployable simplifies local development and lifecycle transactions; internal module boundaries and interface tests are important to avoid coupling. This proposal does not select a broker, worker, ORM, model provider, or cloud platform.
