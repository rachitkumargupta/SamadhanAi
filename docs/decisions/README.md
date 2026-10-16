# Architecture decision log

ADRs record a decision, its context, considered options, consequences, and status. The records below are **proposals for review**, not ratified commitments. Team-wide approval should be recorded by updating the status and decision date.

## Decisions requiring team agreement

- Product owner and authority/city context; policy and data owners.
- MVP roles, identity/anonymous reporting, lifecycle states, transitions, closure verification, appeal/reopen rules.
- Department/jurisdiction source of truth, SLA semantics and values, escalation authority.
- Python/FastAPI and frontend framework/version; JavaScript frontend requirement from brief should be retained unless explicitly changed.
- ORM, migration tool, database version, local development and test database.
- LLM provider/model, LangGraph use/version, data retention/region, prompt/output evaluation and human review thresholds.
- Notification providers/channels and authority-system integration availability.
- API authentication, token/session lifecycle, authorization model, public reference strategy.
- Hosting/deployment, CI, backup, monitoring, availability, privacy/retention obligations.
- Git hosting/default branch, branch protection, review count, commit convention, license.

## Records

- [ADR-001: Technology choices](ADR-001-technology-stack.md)
- [ADR-002: Application architecture](ADR-002-application-architecture.md)
