# Security boundaries and initial threat model

**Status:** Initial design proposal; not a completed security assessment.<br>
**Review owners:** Team Kafka security/privacy representative and relevant authority/policy owner (names TBD).

The project context does not identify the operating authority, jurisdiction, data controller, legal obligations, hosting environment, identity provider, or data classification. This document sets engineering guardrails and threat prompts; it makes no compliance claim and assigns no final risk rating.

## 1. Assets to protect

- Complaint contents, attachments, location, citizen contact details, and identity records.
- Staff identities, permissions, assignments, and administrative capabilities.
- Department/jurisdiction mappings, SLA rules, escalation procedures, and resolution policy.
- Complaint state, event history, resolution evidence, verification records, and audit history.
- Authentication credentials, signing/encryption keys, model/provider credentials, and integration tokens.
- AI prompts, context, structured outputs, evaluation data, and model/run provenance.
- Service availability, notification integrity, and public reference/access mechanisms.

Classify each asset and set retention/access policy before production use.

## 2. Trust boundaries

| Boundary | Untrusted or constrained inputs | Required controls |
|---|---|---|
| Citizen/staff client → API | Request fields, IDs, attachments, browser/session state | Transport security; request/schema/size validation; authentication; server-side action and object-scope authorization; rate limits; safe errors. |
| API/application → database | Application queries, state transitions, migrations | Least-privilege service credentials; repositories; parameterized queries/ORM; transactions and constraints; migration review; backups; scoped access. |
| Application → model provider | Complaint text/context, provider outputs, provider availability | Approved provider and data terms; minimum necessary context; no secrets; bounded calls; output schema/reference validation; retention controls; manual fallback. |
| Agent/orchestrator → tools | Tool arguments and proposed actions | Explicit allowlist; typed arguments; per-tool permission and timeout; application authorization; no arbitrary SQL/shell/network; auditable outcomes. |
| Application → notification provider | Recipient, template, message, delivery responses | Approved channel and consent/preferences; minimal message content; verified destination; scoped credentials; safe retries/idempotency; delivery outcome tracking. |
| Application → authority system | External records, APIs, credentials, failures | Integration must be approved and available; documented contract; allowlisted endpoints; authentication; response validation; timeout/quota controls; audit. |
| Operator/admin → configuration | Roles, reference data, SLA/escalation policy, deployment settings | Separate least-privilege capabilities; approval where policy requires; provenance/version/effective date; review/audit; secret store. |

## 3. Security principles and baseline controls

### Identity and authorization

- Authenticate actors according to the approved user journeys; decide explicitly whether anonymous submission is supported.
- Enforce capability and complaint/resource scope in application services for every protected read and write.
- Do not expose staff-only notes, other citizens’ complaints, internal audit/security details, or unnecessary personal data in public APIs.
- Use least privilege for staff, administrators, service accounts, and automated agents. Keep system administration, policy administration, verification, and audit access distinct where required.
- Define account recovery, deprovisioning, role changes, privileged session controls, and emergency access review before production.

### Data protection and privacy

- Collect only data needed for stated complaint workflows; define purpose, classification, allowed use, retention, correction, deletion, and disclosure.
- Keep secrets outside source control and model prompts. Supply credentials using deployment secret management and define rotation ownership.
- Protect data in transit and at rest using controls supported by the selected hosting/database platform; agree key management and backup encryption.
- Redact or omit personal data and complaint content from operational logs unless specifically necessary and approved.
- Restrict attachment upload and retrieval by file allowlist, size limits, malware/content scanning, isolated storage, and authorization. Do not accept attachments until those controls are designed.
- Do not use real complaint data for model training or evaluation, or send it to a provider, without explicit policy/provider approval.

### Application and database integrity

- Validate and normalize external input; apply body, field, pagination, and upload size limits.
- Use transactions and database constraints for complaint invariants, ownership links, and auditable transitions.
- Use concurrency controls so stale updates cannot silently override current state.
- Keep durable business audit records distinct from operational logs; ordinary users and agents cannot rewrite protected history.
- Make retries safe for complaint creation and provider effects; record failure outcomes accurately.

### AI and agent controls

- Treat complaint text, uploaded/retrieved documents, tool results, and model output as data, not trusted instructions.
- Minimize context, isolate instructions from user-controlled content, and restrict tools to explicit typed operations.
- Validate structured outputs and all referenced category, department, officer/team, jurisdiction, SLA, and policy IDs.
- Application code—not a prompt—decides whether an actor can perform an action or transition.
- Require human review for uncertainty, sensitive/high-impact decisions, missing/conflicting policy, and any action policy designates for approval.
- Bound model time, tokens/cost, retries, and concurrency; define provider outage behavior and manual fallback.

### Integration and availability

- Connect only approved providers. External authority integration availability is unverified.
- Use allowlists, scoped credentials, TLS, strict timeouts, quotas/rate limits, response validation, idempotency, and documented retry rules.
- Do not let notification or model outage corrupt authoritative complaint state; expose pending/failed outcomes to authorized staff.
- Define alerting, incident response, backup, restore, and business continuity expectations before operational release.

## 4. Initial threat scenarios

| ID | Asset / boundary | Threat scenario | Potential impact | Initial mitigation direction | Owner / status |
|---|---|---|---|---|---|
| T-01 | Complaint API and citizen records | Attacker changes complaint ID to read or modify another person's report. | Privacy breach or unauthorized action. | Object-level authorization; non-disclosing errors; authorization tests for owner/staff scopes. | Backend; likelihood/impact rating TBD. |
| T-02 | Accounts and staff roles | Stolen credentials or improper role grant enables privileged access. | Mass exposure, unauthorized assignment/policy changes. | Secure auth lifecycle, least privilege, MFA/stronger admin controls if selected, role-change audit, deprovisioning. | Identity/security owner TBD. |
| T-03 | Attachments | Malicious or oversized file exploits parser/storage or is publicly exposed. | Service compromise, malware, sensitive data disclosure. | Defer attachments until type/size limits, scanning, isolated object storage, and access checks are ready. | Backend/integration; release gate. |
| T-04 | Complaint content → AI | Prompt injection persuades an agent to ignore rules or request an unauthorized tool action. | Data exposure or unauthorized assignment/notification. | Treat content as untrusted, minimize context, typed allowlisted tools, application authorization and output validation. | AI + backend; evaluate before enabling. |
| T-05 | Model output → routing | Hallucinated department, officer, SLA, or urgency is accepted. | Misrouted or delayed complaint; unfair treatment. | Validate all IDs against approved effective references; manual queue for unknown/conflicting data; record provenance. | Backend + policy owner; reference source TBD. |
| T-06 | Administration and policy | Unauthorized or erroneous SLA/routing change alters many cases. | Systemic misrouting, invalid deadlines, hidden policy manipulation. | Separate capability, change approval, version/effective date, impact review, audit and rollback/correction policy. | Policy owner TBD. |
| T-07 | Notifications | Sensitive details sent to wrong, stale, or spoofed destination. | Privacy breach, citizen deception, unsafe response. | Verify recipient/contact changes, use minimal templates, consent/preferences, provider security, delivery audit. | Product/integration; channels TBD. |
| T-08 | Model/integration credentials | Secret committed, logged, included in prompt, or over-scoped. | Provider/account compromise and data exposure. | Secret manager, scoped credentials, redaction, repository scanning, rotation and incident process. | Operations/security owner TBD. |
| T-09 | Public endpoints and provider calls | Automated abuse floods submissions, login, uploads, or expensive AI calls. | Service outage or cost spike. | Rate limits, quotas, abuse monitoring, bounded calls, safe degradation and manual processing. | Operations; thresholds TBD. |
| T-10 | Complaint events and audit | Actor or administrator silently alters history or deletes evidence. | Loss of accountability and inability to investigate. | Append-oriented protected event history, restricted database privileges, audit of administrative access, retention controls. | Backend/operations; tamper-evidence needs TBD. |
| T-11 | External integration | Compromised or malformed provider response is trusted. | Incorrect status/routing, injection, data corruption. | Validate response schema and identity, allowlist endpoints, narrow credentials, contract/failure tests. | Integration owner TBD. |
| T-12 | Data lifecycle | Complaint/AI data retained indefinitely or used beyond stated purpose. | Privacy/legal exposure and loss of trust. | Data inventory, purpose limitation, retention/deletion schedule, provider terms, access review. | Product/policy/security; jurisdiction TBD. |
| T-13 | Service availability | Model, email/SMS, database, or authority provider outage blocks core intake/work. | Complaint loss or missed deadlines. | Keep core lifecycle independent of AI; defined degraded mode, durable records, operational queues, backup/recovery. | Backend/operations; SLO/RTO TBD. |

Risk likelihood and impact are not rated because deployment, threat context, user scale, and jurisdiction are unknown. A security review should prioritize these scenarios with the actual environment and stakeholders.

## 5. Threat-model workflow

Before a production pilot:

1. Identify system owner, data controller/owner, deployment boundary, and data classifications.
2. Map actual data flows, external services, identities, administrative paths, and storage/backup locations.
3. Rate threats by likelihood and impact with the team and relevant authority/privacy stakeholders.
4. Assign an owner and target date to each required control; record accepted residual risks explicitly.
5. Verify authorization, injection, upload, secret, logging, provider-failure, and recovery controls with reviews and tests.
6. Revisit the model when data types, providers, agent tools, roles, or deployment topology change.

## 6. Decisions required before development or release

Some code-level boundaries can be built before all compliance details are final, but production use must wait for decisions on:

- Applicable laws, institutional policies, data controller/processor roles, and breach notification duties.
- Identity proofing, anonymous reporting, staff verification, MFA requirements, token/session lifetime, and account recovery.
- Data classification, collection purpose, access, retention, deletion, correction, subject access, and legal hold.
- Hosting/data region, encryption/key controls, secret manager, backups, RPO/RTO, incident response, and security monitoring.
- Attachment allowance, permitted types, size, scanning, storage, retention, and access.
- AI provider terms, data use/training, retention, region, evaluation data, acceptable quality thresholds, and human approval rules.
- Notification channels, contact verification, consent/preferences, permitted content, and retry policy.
- Security review ownership, vulnerability reporting, dependency updates, and release sign-off.

## 7. Limitations

This is an initial threat model, not penetration testing, a legal assessment, a privacy impact assessment, or a certification. No provider, hosting environment, identity service, or government integration has been verified. Revisit and approve the model with the real operational context before handling real citizen information.
