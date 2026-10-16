# Samadhan AI

Samadhan AI uses multiple AI agents to analyze civic complaints, route them to the appropriate authority, assign SLAs, monitor progress, and escalate delayed cases. LangGraph is proposed for orchestration and RAG for relevant departmental policies, with humans involved in uncertain decisions. These capabilities are planned; the current backend is an initial complaint-intake and tracking slice.

Samadhan AI is a Team Kafka project intended to give citizens a transparent way to submit and track civic complaints, while helping authorized staff route, monitor, and verify resolution. AI recommendations remain subject to approved policy and human review.

## Project status

**Phase 0 documentation is complete.** The first backend slice is scaffolded for citizen complaint submission and owner-scoped tracking. Its dependencies are installed in the local ignored `.venv`, but the app has not been run or verified and its stack choices remain provisional. The initial workspace audit found no source code or dependency manifests. The reference presentation `SamadhanAI.pdf` was not found in the workspace or Desktop tree searched on 2026-10-16.

## Documentation

- [Documentation index](docs/README.md)
- [Backend implementation and setup](backend/README.md)
- [Product requirements](docs/requirements/PRD.md)
- [System architecture](docs/architecture/system-architecture.md)
- [Backend architecture](docs/architecture/backend-architecture.md)
- [AI agent boundaries](docs/architecture/ai-agent-architecture.md)
- [Complaint lifecycle](docs/architecture/complaint-lifecycle.md)
- [Security design](docs/security/security-design.md)
- [API inventory and guidelines](docs/api/api-guidelines.md)
- [Conceptual data model](docs/database/data-model.md)
- [Architecture decision records](docs/decisions/)
- [Development standards](docs/development/standards.md)
- [Roadmap and team boundaries](docs/planning/roadmap.md)

## Setup

See [backend setup instructions](backend/README.md). Framework, database, and authentication choices are provisional. Do not add secrets or real credentials to the repository.

## Contribution

See [CONTRIBUTING.md](CONTRIBUTING.md). Keep pull requests focused, state what was actually verified, and update the relevant requirements and architecture docs as decisions change.
