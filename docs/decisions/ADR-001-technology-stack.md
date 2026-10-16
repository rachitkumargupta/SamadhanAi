# ADR-001: Technology choices

- **Status:** Proposed; pending Team Kafka approval
- **Date:** 2026-10-16
- **Decision owners:** Team Kafka, with backend/AI/frontend workstream input

## Context

The project brief proposes Python/FastAPI, LangGraph, PostgreSQL/pgvector, JWT, RBAC, RAG, MCP, React/JavaScript, Postman, and Git/GitHub. The workspace audit found no manifests or installed project dependencies, and the repository is not initialized as Git. Proposed technologies are not verified commitments.

## Proposal

Use the brief's technologies as candidates for an MVP review. Preserve JavaScript (not TypeScript) for the frontend unless the team explicitly changes that requirement. Select concrete versions, ORM/migration tooling, LLM provider, testing/linting tools, and deployment only after compatibility, policy, cost, and operational needs are reviewed. Defer pgvector, MCP, and RAG until approved knowledge retrieval/integration requirements justify them.

## Consequences

No dependency installation or external service commitment is made by this ADR. The team must decide version support, licenses, provider data handling, local setup, CI, and maintainers before implementation. Python/FastAPI and PostgreSQL remain proposals pending approval.
