# Non-functional requirements

**Status:** Draft for Team Kafka review<br>
**Related documents:** [PRD](PRD.md), [functional requirements](functional-requirements.md), [security design](../security/security-design.md)<br>
**Version:** 0.1

Non-functional requirements (NFRs) describe the quality, safety, and operational properties of the system. The requirements below are proposals. Numeric service targets are intentionally marked **TBD** where traffic, hosting, authority policy, or operational ownership is unknown. Before production, owners must replace TBD targets with measurable, testable commitments.

## Security and privacy

| ID | Priority | Requirement | Acceptance / verification approach | Decisions needed |
|---|---|---|---|---|
| NFR-SEC-01 | Must | Enforce least privilege and resource-level authorization for every protected operation. | Security tests cover permitted and denied role/scope combinations, including direct object-ID substitution. | Approved roles, scope model, auth provider and session/token lifecycle. |
| NFR-SEC-02 | Must | Protect secrets and credentials from source control, client bundles, logs, and model context. | Repository/config review finds no real secrets; automated secret scanning and log/context redaction checks are defined before release. | Secret manager and rotation ownership. |
| NFR-SEC-03 | Must | Protect data in transit and at rest using controls supported by the chosen deployment platform. | Deployment configuration and security review verify transport protection and storage encryption/key management. | Hosting platform, key ownership/rotation, backup encryption. |
| NFR-SEC-04 | Must | Minimize personal and sensitive data collection, display, logging, and retention. | Field inventory, access projections, log review, and retention/deletion behavior are approved and verified. | Data classification, applicable legal/institutional policy, retention schedule, deletion exceptions. |
| NFR-SEC-05 | Must | Treat user inputs, attachments, external responses, retrieved content, and AI outputs as untrusted. | Validation, attachment safeguards, integration response checks, and AI output schema/permission tests demonstrate rejection or safe review of invalid data. | Allowed file types/limits and threat review owner. |
| NFR-SEC-06 | Must | Preserve attributable, tamper-resistant records of privileged actions and material lifecycle decisions. | Audit tests verify actor, timestamp, action, target, and reason/reference; ordinary users and agents cannot alter protected history. | Audit retention, access, export, and tamper-evidence requirements. |
| NFR-SEC-07 | Must | Keep AI tools narrowly scoped and subject to application authorization. | Tool registry and integration tests show agents cannot access arbitrary SQL/network/actions and cannot bypass server-side permission checks. | Human-approval thresholds, provider data handling, model retention/region. |

## Reliability and data integrity

| ID | Priority | Requirement | Acceptance / verification approach | Decisions needed |
|---|---|---|---|---|
| NFR-REL-01 | Must | A complaint registration and its required initial history record must succeed or fail atomically. | Failure-injection/database tests verify there is no reported success with a partial record. | Database and transaction strategy. |
| NFR-REL-02 | Must | Retries of requests and external side effects must not create unintended duplicate records or actions. | Idempotency behavior is contract-tested for applicable writes and provider retries. | Key scope and retention, provider deduplication capabilities. |
| NFR-REL-03 | Must | Provider or model failure must not corrupt complaint state or silently authorize a fallback decision. | Timeout, malformed-response, and outage tests verify safe failure, visible status, and manual handling path. | Outage operating procedure and recovery ownership. |
| NFR-REL-04 | Must | Concurrent updates must preserve lifecycle invariants and expose conflicts. | Concurrent transition tests demonstrate conflict detection or safe serialization; no silent lost update occurs. | Optimistic/pessimistic concurrency mechanism and client conflict UX. |
| NFR-REL-05 | Must | The service must have defined backup, restore, and recovery objectives before production use. | Restore rehearsal demonstrates agreed recovery point and recovery time objectives. | RPO, RTO, backup frequency, retention, owner, and hosting. |

## Performance and capacity

| ID | Priority | Requirement | Acceptance / verification approach | Decisions needed |
|---|---|---|---|---|
| NFR-PERF-01 | Must | User-facing API response-time objectives must be defined for normal and peak load. | Load tests against representative workload meet approved p95/p99 targets by endpoint class. | Expected concurrent users, request rates, payload sizes, and target latency. |
| NFR-PERF-02 | Must | Complaint submission and tracking should remain usable when AI or notification providers are slow or unavailable. | Dependency delay/failure tests show bounded request time and the agreed degraded behavior. | Whether analysis is synchronous, queue/worker design, intake acknowledgment semantics. |
| NFR-PERF-03 | Should | Long-running analysis, monitoring, and integration tasks must have explicit time, concurrency, and resource limits. | Load tests and operational limits prevent unbounded work and protect core API capacity. | Expected AI volume, model limits/cost budget, scheduling needs. |
| NFR-PERF-04 | TBD | The system should support the expected complaint, attachment, and audit-history growth for the agreed retention period. | Capacity estimate and representative storage/load test confirm adequate indexes and storage. | Launch volume, growth, attachment profile, retention and deletion rules. |

No numeric traffic or latency target is asserted in this draft. Record targets and workload assumptions here or in an approved service-level document before a release candidate.

## Availability and operability

| ID | Priority | Requirement | Acceptance / verification approach | Decisions needed |
|---|---|---|---|---|
| NFR-OPS-01 | Must | Production availability objectives and maintenance expectations must be defined and observable. | Monitoring reports service health against approved SLOs and maintenance policy. | Hosting, support hours, availability target, maintenance windows. |
| NFR-OPS-02 | Must | Operators must be able to diagnose failures using correlation IDs, structured logs, and relevant health signals. | A representative incident can be traced across API, database, and provider boundaries without exposing unnecessary PII or secrets. | Logging/metrics platform, alert thresholds, access and retention. |
| NFR-OPS-03 | Must | Readiness and liveness signals must reflect the intended deployment behavior without leaking sensitive topology. | Deployment checks distinguish a process that is alive from one ready to serve its required workload; endpoints disclose no credentials or internals. | Deployment platform and dependency readiness policy. |
| NFR-OPS-04 | Must | Operational procedures must cover provider outage, failed notification, migration failure, suspected data exposure, and recovery. | Runbooks identify owner, safe steps, escalation route, and post-incident records before production. | Operations owner, incident contact path, severity model. |
| NFR-OPS-05 | Should | Application changes to persistent schema must be migration-managed and recoverable. | Fresh setup and upgrade paths are exercised against supported database versions; rollback/forward-fix approach is documented. | ORM, migration tool, database version, deployment sequence. |

## Usability and accessibility

| ID | Priority | Requirement | Acceptance / verification approach | Decisions needed |
|---|---|---|---|---|
| NFR-UX-01 | Must | Citizens must receive understandable confirmation, status, and next-step guidance in plain language. | Representative users can complete agreed tasks; content review covers errors, requests for information, and resolution notices. | User research participants, language and literacy needs. |
| NFR-UX-02 | Must | Citizen and staff experiences must support the accessibility standard selected by the team. | Automated and manual accessibility review covers keyboard use, screen readers, contrast, focus, labels, and error feedback against the chosen standard. | Applicable standard/level and review owner. |
| NFR-UX-03 | Should | The interface should support the agreed devices, browsers, and languages. | Compatibility and language tests cover the supported matrix. | Browser/device baseline, language set, translation ownership, right-to-left needs. |

## Maintainability and interoperability

| ID | Priority | Requirement | Acceptance / verification approach | Decisions needed |
|---|---|---|---|---|
| NFR-MNT-01 | Must | API, domain rules, persistence, AI orchestration, and external integrations must have explicit boundaries. | Code review and architecture checks show route handlers do not own domain policy, agents do not bypass application services, and provider SDKs remain behind adapters. | Package layout and dependency rules. |
| NFR-MNT-02 | Must | Public and internal API contracts must be documented and version changes managed deliberately. | OpenAPI/schema review and contract tests detect breaking changes; version/deprecation policy is published. | API versioning and compatibility window. |
| NFR-MNT-03 | Must | Builds and relevant automated checks must be repeatable from documented setup instructions. | A clean environment can follow setup and run the agreed checks using pinned supported tools. | Runtime versions, package manager, CI service, test/lint tools. |
| NFR-INT-01 | Must | External adapters must have bounded timeouts, explicit failure mapping, and allowlisted operations. | Contract/failure tests cover success, malformed response, timeout, rate limit, and provider outage. | Integration inventory, owners, provider contracts and quotas. |
| NFR-INT-02 | TBD | Data exchange with any authority system must meet that system's approved security and contract requirements. | Integration review and end-to-end tests pass against an authorized sandbox before production credentials are considered. | Whether any system exists/is accessible, API specs, legal approvals, sandbox access. |

## AI quality and governance

| ID | Priority | Requirement | Acceptance / verification approach | Decisions needed |
|---|---|---|---|---|
| NFR-AI-01 | Must | AI outputs used by the application must be schema-validated and checked against approved reference data and domain rules. | Invalid schema, unknown identifiers, and policy conflicts are rejected or sent to review in tests. | Schema owner, taxonomy and validation policy. |
| NFR-AI-02 | Must | Material AI-assisted decisions must be traceable to agent/schema/model version and human disposition where applicable. | A reviewer can inspect permitted provenance and distinguish suggestion from applied action. | Audit detail, privacy/retention, provider metadata. |
| NFR-AI-03 | Must | AI assistance must have a defined manual fallback for unavailable, low-confidence, or disallowed outputs. | Scenario tests show staff can complete the lifecycle without an AI response; fallback workload is understood. | Review queue ownership, confidence/review rules. |
| NFR-AI-04 | Must | AI quality must be evaluated on approved representative data before material release or model/prompt changes. | Evaluation protocol, data governance, thresholds, regression suite, and review sign-off are documented. | Dataset owner, quality metrics, fairness/impact review, release authority. |
| NFR-AI-05 | Should | AI prompts/context should use the minimum data required for the task and avoid unnecessary personal information. | Context inspection and privacy review confirm minimization and appropriate provider configuration. | Provider terms, data region, retention/training policy. |

## Release readiness checklist for NFR decisions

Before production, the team should approve and make testable:

1. Supported user/device/language and accessibility expectations.
2. Workload model, performance targets, capacity assumptions, and data retention period.
3. Availability objective, support hours, incident ownership, RPO, and RTO.
4. Data classification, applicable legal/institutional duties, access, deletion, audit, and backup policy.
5. Authentication, secret management, encryption/key controls, security review, and incident response.
6. Provider/model timeout, quota, cost, data handling, and manual fallback expectations.
7. Integration contracts, operational limits, and authorization for each external system.

## Change control

Keep NFR IDs stable. Each approved NFR should have an accountable owner, a measurable target or explicit rationale for a qualitative control, and a verification method. Update the PRD summary and architecture/security docs when an approved target changes. Do not mark a target satisfied until the corresponding evidence exists.
