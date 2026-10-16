# Roadmap and team workstream boundaries

This is a sequencing proposal, not an assignment of named people or a committed schedule. Team availability and ownership are unknown.

## Suggested milestones

1. **Phase 0 — Foundation:** review PRD, lifecycle, roles, ADRs, security questions, reference PDF, and working agreements.
2. **Phase 1 — Policy and contracts:** confirm state machine, authorization matrix, data ownership, API contract, conceptual schema, identity and closure policy.
3. **Phase 2 — Manual end-to-end lifecycle:** implement intake, tracking, staff/department data, assignment, status history, resolution/verification, and core tests without requiring AI.
4. **Phase 3 — Operational controls:** add approved SLA configuration, monitoring/escalation handling, notifications, audit/admin visibility, and failure/retry behavior.
5. **Phase 4 — Bounded AI assistance:** integrate structured analysis/routing recommendations behind schemas, reference-data checks, human review, fallback, and quality evaluation.
6. **Later scope:** evaluate duplicate consolidation, heatmaps, predictive maintenance, dynamic allocation, voice/multilingual reporting, IoT, external government integrations, and broader analytics against evidence and policy.

## Workstream boundaries

- **Product/policy coordination:** owns user outcomes, approved taxonomies, status/verification policy, SLA and jurisdiction sources, acceptance criteria.
- **Frontend:** owns citizen/staff/admin experiences, accessibility, client-side validation and API integration; backend remains responsible for authorization and validation.
- **Backend:** owns API contracts, identity/authorization enforcement, domain lifecycle, persistence/migrations, transactions, audit, integration interfaces, and operational behavior.
- **AI:** owns agent prompts/contracts/orchestration and evaluation proposals; backend/application retains authority over permissions, writes, and policy rules.
- **Integration/operations:** owns approved provider connectivity, credentials, environment/deployment, monitoring, backups, and provider failure handling in coordination with backend.
- **Testing/quality:** collaborates across workstreams on acceptance, contract, security, data, and end-to-end checks.

These are responsibility boundaries only. Assign individuals after the team shares its actual membership and preferences.
