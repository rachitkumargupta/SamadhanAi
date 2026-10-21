# MVP scope and release boundary

**Status:** Target scope from the supplied blueprint; operational policies and release targets require team/authority approval.<br>
**Related:** [PRD](PRD.md), [functional requirements](functional-requirements.md), [NFRs](non-functional-requirements.md), [master implementation blueprint](../architecture/implementation-blueprint.md)

## MVP outcome

Demonstrate an image-first civic complaint lifecycle from persistence and AI-assisted triage through validated departmental work, deterministic SLA processing, evidence-backed resolution, and citizen confirmation or independent dispute review. AI or notification outages must not lose a complaint or authorize an unsupported action.

## Included target capabilities

| Capability | MVP boundary |
|---|---|
| Intake and access | Required image; optional citizen description; secure tracking; anonymous submission with a high-entropy secret, protected verifier, rate limits and non-enumerating access responses. |
| Location | Explicit GPS permission or manual map selection, accuracy/source metadata, and jurisdiction lookup from configured boundaries. No fabricated coordinates or image-derived jurisdiction. |
| Media | Decoded-content validation; configured type/size/dimension limits; safe normalization and metadata handling; private object storage; access control; scanning and retention policy before real-user enablement. |
| Analysis | Durable asynchronous Complaint Analyst job after persistence; typed findings for grounded description, category, priority/severity recommendation, visible evidence, uncertainty, missing information, multi-department need, and review. Initial configurable categories: roads/potholes; garbage/sanitation; drainage/sewage; water/leakage; streetlights/electrical; damaged public infrastructure; other/uncertain. Deterministic rules validate priority and handle emergency/safety-critical cases. Human/manual fallback. |
| Routing and work | Resolution & Routing recommendations checked against approved department/jurisdiction/officer/policy records; human review for conflicts; parent plus independently assigned child tickets for composite work. |
| SLA and escalation | Persist policy-versioned deadlines per child; scheduled deterministic batched worker; idempotent breach events and downtime recovery. Monitoring & Escalation runs only for event-driven reasoning. |
| Resolution and verification | Officer evidence submission remains pending; notify the citizen and provide a proof card with confirm/dispute actions; at 48 hours without response send a reminder and keep pending; silence does not confirm. Disputes enter an assigned Independent Reviewer queue. No response by 7 calendar days from verification start routes the still-open case to that queue for reasoned review under the intended project policy. Parent closure normally waits for all child workflows; exceptional closure requires Senior Authority permission and an audit record. |
| Notifications and audit | Durable in-app notices for receipt, analysis/review, assignments, information requests, progress, SLA warnings/escalations, resolution, verification reminders/decisions, and final review; retry outcomes, actor-attributed events, agent provenance, and auditable privileged actions. Email is optional. |
| Operations | Reproducible setup, migrations, logs/health, retry/recovery procedures, and tested deployment limits. No continuous-monitoring or production-readiness claims without evidence. |

Exactly three core agents are in scope: Complaint Analyst, Resolution & Routing, Monitoring & Escalation. Deterministic backend code retains authority for permissions, reference validation, ticket creation, deadlines, state transitions, and side effects.

## Excluded from initial MVP

- Duplicate detection or automatic consolidation/merging.
- Heatmaps, predictive maintenance, dynamic SLA/resource allocation, and city-wide analytics.
- Multilingual/voice reporting, IoT, and live municipal integrations unless separately approved and supported.
- Autonomous AI rejection, assignment override, closure, or deadline polling.
- Extra core agents, arbitrary agent tools, decorative MCP, or unnecessary microservices/infrastructure.

## Release gates

1. Approve role grants/separation, anonymous-token security operations, jurisdiction/source data, normalized state names/transitions, SLA policies, escalation hierarchy, evidence rules, and reminder delivery. The 48-hour decision window, reminder at expiry, pending status, prohibition on treating silence as confirmation, and seven-calendar-day overdue-review threshold are intended project requirements. Late responses before reviewer assignment follow ordinary verification; during active review they remain visible to the reviewer, cannot auto-close/cancel review, and a late dispute does not automatically reprioritize. Before implementation, approve reviewer authority/outcomes and mapping to the actual municipal authority, the jurisdiction's daylight-saving ambiguity rule, and downtime recovery details.
2. Image upload, storage, scanning, privacy and model-provider handling pass security review.
3. Complaint persistence is independent of AI; asynchronous work, jobs/events, and retries are durable and idempotent.
4. Composite tickets maintain independent assignment, state, SLA and history; parent aggregation does not conceal unresolved children.
5. Deterministic SLA processing handles the 10,000-active-ticket test scenario without per-ticket model calls, recovers after downtime, and avoids duplicate breaches/escalations.
6. Authorization is verified for citizen, officer, administrator, and independent reviewer scopes.
7. Resolution cannot close immediately; after 48 hours without a citizen decision, send a reminder and keep the ticket pending; disputes route to independent review and silence never implies confirmation. Verify the intended seven-day overdue handoff and authorized reviewer outcomes without treating silence as proof of resolution.
8. Notifications, backups, recovery, performance, accessibility, data retention, and hosting behavior meet approved targets.
9. Critical acceptance tests pass and docs match the shipped behavior.

These gates are target criteria, not claims that implementation exists.

## Critical acceptance scenarios from the blueprint

1. **SLA scale:** process at least 10,000 active tickets using deterministic indexed deadline queries without an LLM call per ticket.
2. **Downtime recovery:** restart the worker and recover overdue work.
3. **Idempotency:** reprocess a breach event without duplicate logical escalation.
4. **Composite routing:** create independently assigned child tickets with separate SLA clocks for a multi-department issue.
5. **Jurisdiction conflict:** prevent repeated department rejection from creating an uncontrolled loop.
6. **Parent aggregation:** reflect child progress without hiding unresolved children.
7. **Closure protection:** officer resolution does not close the ticket immediately.
8. **Citizen dispute:** route a disputed resolution to independent review.
9. **No response:** at the 48-hour boundary, send one idempotent reminder and keep the complaint pending. At the seven-calendar-day boundary, create one overdue-review case and route it to an Independent Reviewer under the intended policy; verify before/at/after-boundary behavior, worker recovery, and stale-response handling. Never treat silence alone as confirmation.
10. **Review independence:** prevent the original officer from acting as the sole reviewer of their resolution; enforce assigned reviewer scope and explicitly granted decision transitions.
11. **Authorization:** deny unauthorized reassignment, override, closure, and audit access, including ungranted Senior Authority/Independent Reviewer actions.

## Open decisions

Anonymous token encoding, key storage/rotation, expiry/renewal, rate limits and recovery channel; official category/jurisdiction/department sources; model/provider and data terms; object storage/scanning and retention; SLA calendars/values and scheduler deployment guarantees; role scopes and mapping Independent Reviewer/Senior Authority to actual governance; reminder delivery; reviewer authority/outcomes and daylight-saving ambiguity rule; notification channel; and production obligations. Lost anonymous tokens have no account-style recovery without independent identity proof. Demonstration policies must be clearly labelled and never presented as official rules.
