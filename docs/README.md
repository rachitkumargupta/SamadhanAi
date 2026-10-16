# Samadhan AI documentation

This is the Phase 0 documentation baseline, drafted from the project brief on 2026-10-16. The local workspace initially had no source code or Git metadata. These documents describe proposals and planning contracts; they do not assert that integrations, policy data, or production infrastructure exist.

## Phase 0 readiness

**Documentation foundation: complete enough to begin the first development slice.** Do not expand documentation for its own sake. Add documents such as a detailed data dictionary, migration runbook, deployment guide, or troubleshooting guide when implementation choices and actual operating procedures exist.

**Development status:** The first backend slice for citizen complaint intake and owner-scoped tracking is scaffolded under [`backend/`](../backend/README.md), including list and citizen-visible event-history routes. It has not been run or verified, and its toolchain remains provisional.

Before coding the complaint lifecycle, the team should agree on the minimum blocking decisions: (1) initial roles and complaint access rules, (2) first lifecycle states and who may transition them, (3) required complaint fields and initial classification/department source, (4) resolution verification and closure rule, and (5) backend/database/tool versions for the first slice. Other integrations, AI provider choices, advanced features, and production targets can be decided when their work is scheduled.

## Contents

- [Requirements and MVP](requirements/PRD.md)
- [Functional requirements](requirements/functional-requirements.md)
- [Non-functional requirements](requirements/non-functional-requirements.md)
- [MVP scope](requirements/MVP-scope.md)
- [Roles and use cases](requirements/user-roles-and-use-cases.md)
- [System architecture](architecture/system-architecture.md)
- [Backend structure](architecture/backend-architecture.md)
- [AI agent interfaces](architecture/ai-agent-architecture.md)
- [Complaint lifecycle](architecture/complaint-lifecycle.md)
- [Security design and threat prompts](security/security-design.md)
- [API guidelines and endpoint inventory](api/api-guidelines.md)
- [API error-handling contract](api/error-handling.md)
- [Conceptual data model](database/data-model.md)
- [Decisions and approvals](decisions/README.md)
- [Development standards](development/standards.md)
- [Roadmap and workstream boundaries](planning/roadmap.md)

## Status conventions

“Proposed” means a starting recommendation that needs team review. “Pending” means the project brief does not supply enough information to decide. Policy-specific values and integration availability must come from authorized sources, not assumptions.

## Reference material

`SamadhanAI.pdf` was not found under the project folder or Desktop tree searched during the initial audit. The architecture and future-scope descriptions in these docs come from the supplied project brief only. Add the presentation under `docs/reference/` after the team provides it; do not alter the original.
