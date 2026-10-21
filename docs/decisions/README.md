# Architecture decision log

ADRs record chosen direction and remaining approval work. Current baseline is the supplied [master implementation blueprint](../architecture/implementation-blueprint.md); the documents below distinguish target recommendations from approved provider, policy, and deployment choices.

## Key approvals still needed

- Citizen identity integration and the security/operations details for the supported anonymous tracking flow; staff JWT issuer, role scopes, and independent-review separation.
- Official departments, wards/jurisdiction boundaries, category taxonomy, SLA/escalation values/calendars, evidence rules, role mapping, reminder delivery, and reviewer authority/outcomes. Anonymous submission/tracking and the seven-calendar-day overdue-review threshold are intended project policies. The 48-hour decision window, reminder with pending status after silence, and prohibition on closure by silence are fixed. Late responses are preserved for an active reviewer and cannot auto-close/cancel review; late disputes do not automatically reprioritize. Specify the jurisdiction's daylight-saving ambiguity rule and security/operations choices before production.
- Image storage/scanning/retention, model provider and image-data terms, LangGraph persistence, and evaluation criteria.
- Scheduled worker/job-claiming mechanism and hosting guarantees, notification channels, production support, backup/recovery/SLOs.
- Concrete runtime/package versions, CI/test/lint tools, frontend setup, and API compatibility process.

## Records

- [ADR-001: Recommended technology stack](ADR-001-technology-stack.md)
- [ADR-002: Modular-monolith application architecture](ADR-002-application-architecture.md)
