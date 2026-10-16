# MVP scope and release boundary

**Status:** Draft for Team Kafka approval<br>
**Related:** [PRD](PRD.md), [functional requirements](functional-requirements.md), [non-functional requirements](non-functional-requirements.md), [roles and use cases](user-roles-and-use-cases.md)

## MVP outcome

The MVP is a usable, auditable end-to-end complaint lifecycle: an eligible citizen can submit and track a complaint; authorized staff can review, route, assign, work, and record evidence; the system can apply approved SLA rules, record notifications/escalations, and enforce an approved verification policy before closure.

The MVP is not defined by how many AI capabilities it contains. It must remain operational when an AI provider is unavailable. Manual review and configuration-backed rules are acceptable ways to complete the first lifecycle, provided they are explicit and traceable.

## Included capabilities

| Capability | MVP boundary | Related requirements |
|---|---|---|
| Identity and access | Approved citizen/staff/admin access model; server-side role and complaint-scope authorization. Anonymous reporting is excluded until explicitly approved. | FR-IAM-01–04 |
| Complaint intake | Validate required fields, register atomically, issue a stable public reference, and record initial history. | FR-CMP-01–03, FR-CMP-07 |
| Attachments | Optional only if approved storage, size/type limits, access controls, and scanning/retention decisions are ready. Otherwise omit from initial release and clearly communicate this in intake UX. | FR-CMP-04 |
| Tracking | Actor-scoped complaint detail and bounded, paginated lists with citizen-safe status/history. | FR-CMP-05–07 |
| Analysis | Initially support manual triage or bounded structured suggestions; enforce schema and reference checks; preserve manual path. Missing-information requests are recorded. | FR-ANL-01–05 |
| Organization and routing | Maintain approved department/jurisdiction/team reference data. Route by reviewed mapping or send to a human triage queue. No invented destinations. | FR-ROU-01–05 |
| Assignment and work | Authorized assignment/reassignment, progress updates, allowed lifecycle transitions, and attributable history. | FR-LCY-01–02 |
| SLA and escalation | Apply approved effective-dated rules and identify due/overdue work. Escalation findings/actions are recorded; manual review/notification is acceptable initially. | FR-SLA-01–02, FR-ESC-01–02 |
| Notifications | At least persist intended notification and outcome records. External delivery is MVP only if a channel/provider is approved and safely configured; otherwise clearly expose delivery limitation to staff. | FR-NOT-01–02 |
| Resolution and closure | Record resolution evidence and require approved verification before closure; preserve reject/reopen route defined by policy. | FR-CLS-01–03 |
| Administration and audit | Authorized maintenance/inspection for the reference data and queues needed by the lifecycle; protected event history for material actions. | FR-ADM-01–02, FR-AUD-01 |
| Operations | Documented environment setup, configuration, safe logging, migrations, backup/recovery approach, and agreed release checks. No production readiness claim until NFR decisions are approved and verified. | NFR-SEC-*, NFR-REL-*, NFR-OPS-* |

## Explicitly excluded from initial MVP

Unless a product/policy owner approves a change with updated requirements and acceptance criteria, the MVP excludes:

- Automatic duplicate complaint consolidation or merging.
- Geographic heatmaps and city-wide analytics.
- Predictive maintenance or forecasting.
- Dynamic SLA or resource allocation.
- Multilingual and voice-based reporting beyond any manually selected initial language support.
- IoT/smart-city integrations.
- Live government or municipal system integrations; their existence and access are unverified.
- General-purpose MCP tool ecosystems or arbitrary agent tool execution.
- Autonomous rejection, assignment override, enforcement action, or complaint closure by an LLM.
- Microservices, Kafka, Redis, Celery, Kubernetes, or other infrastructure without a documented need.
- Advanced RAG/vector search until approved knowledge sources and a retrieval requirement exist.

## Release gates

The MVP is eligible for a release review only when all of the following are satisfied:

1. Team approves the role/authorization matrix, complaint states and transitions, citizen visibility rules, SLA semantics, and closure verification/reopen policy.
2. Approved department/jurisdiction/routing data has a named owner, provenance, and a human path for missing mappings.
3. Core lifecycle works without AI and without any external notification/authority provider being available.
4. Complaint registration, state transitions, and audit history preserve agreed transactional and concurrency invariants.
5. Authorization tests cover citizen ownership and staff/admin scopes; sensitive operations cannot be invoked by an unapproved agent/tool.
6. AI-enabled steps, if present, validate structured output and reference data, record provenance, and fall back to manual review on error/uncertainty.
7. Notification delivery behavior is honest about pending/failed outcomes and safe to retry.
8. Applicable security, privacy, accessibility, performance, backup, recovery, and operational targets are agreed and verified for the target deployment.
9. Documentation, API contracts, setup, migration, operator procedures, and known limitations match the shipped behavior.

These gates do not assert that implementation or verification exists yet.

## MVP completion scenarios

At minimum, acceptance walkthroughs should demonstrate:

- A citizen submits a valid report, gets a reference, and sees only permitted tracking information.
- An invalid or unauthorized request is safely rejected without partial or cross-user data exposure.
- A complaint with missing information can be returned for details and resume review after the response.
- A complaint with no valid route enters a visible triage queue rather than receiving an invented assignment.
- Authorized staff can assign, update, submit resolution evidence, and receive an allowed verification decision with history.
- A due/overdue case is identified from an approved SLA rule; escalation/notification result can be inspected.
- AI/provider failure does not block the manual lifecycle or cause an unauthorized state change.

## Scope-change process

Any request to add an excluded feature or change a release gate should identify the user need, policy/data source, security and privacy impact, operating cost, dependencies, and measurable acceptance criteria. Update the PRD, functional/NFR traceability, architecture/ADR, and roadmap before treating the change as committed MVP scope.

## Decisions blocking final scope approval

- Initial citizen identity and anonymous-report policy.
- Required attachments and approved storage/security capability.
- Actual lifecycle states, staff roles, and separation of duties.
- Approved classifications, departments, jurisdictions, SLA and escalation policies.
- Required notification channel(s) and whether delivery is mandatory for MVP.
- Applicable privacy/legal/accessibility obligations and target operating environment.
- Whether structured AI suggestions are in MVP or whether the first lifecycle is fully manual.
