# Samadhan AI

Samadhan AI is a civic complaint workflow platform. Its target is image-first citizen reporting followed by structured AI assistance, validated departmental work, deterministic SLA monitoring, and evidence-backed citizen verification. Application code retains authority for permissions, routing validation, state changes, deadlines, notifications, and audit.

The target has exactly three core agents: Complaint Analyst, Resolution & Routing, and Monitoring & Escalation. Complaints involving multiple departments use a parent record and independently tracked child tickets. SLA deadlines are processed by a deterministic recoverable worker; the escalation agent is invoked by valid events, not continuous polling. See the [master implementation blueprint](docs/architecture/implementation-blueprint.md).

## Current implementation status

The backend has authenticated image-first intake, normalized private local media storage, durable asynchronous Complaint Analyst processing, and owner-scoped tracking. The Agent 3 slice now includes assigned-officer resolution-proof upload and protected proof viewing; it changes the complaint to `resolved_pending_verification` without closing it. Citizen decisions, reviewer decisions, automatic SLA-case registration, and production storage remain incomplete. Current environment and endpoints are listed in [backend README](backend/README.md).

## Documentation

- [Documentation index](docs/README.md)
- [Product requirements and MVP scope](docs/requirements/PRD.md)
- [Functional requirements](docs/requirements/functional-requirements.md)
- [System architecture](docs/architecture/system-architecture.md)
- [Backend architecture](docs/architecture/backend-architecture.md)
- [Three-agent contracts](docs/architecture/ai-agent-architecture.md)
- [Complaint lifecycle](docs/architecture/complaint-lifecycle.md)
- [Conceptual data model](docs/database/data-model.md)
- [Security design](docs/security/security-design.md)
- [API contract guidance](docs/api/api-guidelines.md)
- [Decisions and roadmap](docs/decisions/README.md) · [Roadmap](docs/planning/roadmap.md)

## Setup and contribution

See [backend setup instructions](backend/README.md) and [contribution guidelines](CONTRIBUTING.md). Do not commit secrets, real complaint data, or database dumps. Label demo policy data as non-official. Update requirements and architecture when decisions change, and distinguish implemented behavior from the target blueprint.
