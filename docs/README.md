# Samadhan AI documentation

This documentation set is aligned to the supplied **Complete Project Specification & Implementation Blueprint** on 2026-10-21. [Master implementation blueprint](architecture/implementation-blueprint.md) is the cross-document baseline. It describes the target, not proof of implementation. Product/privacy decisions explicitly marked pending must be approved before real-user/production use.

## Current status

The backend is a preliminary text-based citizen complaint intake/tracking slice. It does not yet implement image upload, GPS/manual map capture, async analysis, routing, child tickets, SLA worker, escalation, staff/admin interfaces, notifications, or verification. Check [backend setup and implementation status](../backend/README.md) and [roadmap](planning/roadmap.md) before treating any target capability as complete.

## Contents

- [Master implementation blueprint](architecture/implementation-blueprint.md)
- [Product requirements](requirements/PRD.md)
- [Functional requirements](requirements/functional-requirements.md)
- [Non-functional requirements](requirements/non-functional-requirements.md)
- [MVP scope and release gates](requirements/MVP-scope.md)
- [Roles and use cases](requirements/user-roles-and-use-cases.md)
- [System architecture](architecture/system-architecture.md)
- [Backend architecture](architecture/backend-architecture.md)
- [Three-agent contracts](architecture/ai-agent-architecture.md)
- [Complaint lifecycle](architecture/complaint-lifecycle.md)
- [Conceptual data model](database/data-model.md)
- [Security design](security/security-design.md)
- [API guidelines](api/api-guidelines.md)
- [API error handling](api/error-handling.md)
- [Architecture decisions](decisions/README.md)
- [Development standards](development/standards.md)
- [Roadmap and workstream boundaries](planning/roadmap.md)

## Status conventions

“Target” reflects the supplied blueprint. “Proposed” or “pending approval” means a policy, provider, deployment or operational owner still needs to decide. “Implemented” is reserved for code present in the repository; “verified” requires recorded checks. Demonstration policies must be labelled and must not be presented as official municipal rules.
