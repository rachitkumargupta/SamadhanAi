# User roles and use cases

**Status:** Draft for Team Kafka review<br>
**Depends on:** [PRD](PRD.md)<br>
**Policy note:** Role names and capabilities below are proposals. The organization, identity model, and applicable policies have not yet been confirmed.

## Actors

| Actor | Purpose | Trust and access boundary |
|---|---|---|
| Citizen | Report a civic issue and follow its progress | May access only complaints they are permitted to access; anonymous reporting and identity proofing are undecided. |
| Case officer | Investigate and update assigned work | May access assigned or otherwise authorized complaints and perform permitted actions within their scope. |
| Department supervisor | Manage a department queue and respond to escalations | May view and reassign work only within an approved department/jurisdiction scope. |
| System administrator | Maintain user access and operational configuration | Administrative access is privileged and must be narrowly scoped and audited. |
| Policy administrator | Maintain approved taxonomy, routing references, SLA rules, and escalation policies | Policy changes require provenance, effective dates/versioning, and an agreed approval process. Whether separate from system administrator is TBD. |
| Automated service / AI agent | Propose analysis, routing, monitoring, or notification actions | Not a human identity or authority role. It can invoke only explicitly allowed interfaces; application authorization and policy checks remain authoritative. |

Support/auditor and verifier may become distinct roles if separation-of-duties, institutional, or legal requirements call for them. Do not assume those roles are combined with administrators or officers.

## Authorization principles

- Authenticate the actor where the approved user journey requires it; define anonymous access explicitly before accepting anonymous submissions.
- Authorize every operation on the server using both capability and resource scope. A role name alone must not grant access to every complaint.
- Keep citizen-visible status/history separate from internal notes, security events, and staff-only data.
- Treat assignment, policy changes, verification, closure, and administrative access as auditable actions.
- AI output is never a role, permission, or authorization grant. Agent proposals pass through the same application rules as other inputs.
- Define how access is removed, staff roles are changed, conflicts of interest are handled, and privileged emergency access is reviewed.

## Use cases

### UC-01 — Submit a complaint

**Primary actor:** Citizen<br>
**Preconditions:** Submission policy and required fields are configured; any required identity step is complete.<br>
**Main flow:** Citizen enters complaint details and optional evidence; the system validates input, registers a record and audit event, generates a reference, and returns an acknowledgement.<br>
**Alternate flows:** Invalid input receives safe field-level guidance. Attachment rejection does not silently discard the complaint text. Duplicate/idempotent retries return a safe result without unintended duplicate records. If analysis is unavailable, registration can still succeed if policy permits.<br>
**Open decisions:** Anonymous reports, required fields, attachment limits, public reference format, rate limits, and whether intake can be accepted during downstream outages.

### UC-02 — Track a complaint

**Primary actor:** Citizen<br>
**Preconditions:** Citizen has authenticated or completed the approved reference/access proof.<br>
**Main flow:** Citizen requests a complaint view and sees permitted current status, timestamps, and citizen-visible events.<br>
**Alternate flows:** Unauthenticated, expired, or unauthorized access receives a non-disclosing response. Internal notes and other citizens’ data are never exposed.<br>
**Open decisions:** Login versus reference-based access, identity recovery, history visibility, and disclosure policy.

### UC-03 — Request and provide missing information

**Primary actors:** Authorized officer/system workflow; citizen<br>
**Preconditions:** Complaint is in a state where information can be requested.<br>
**Main flow:** Authorized staff or an approved rule records a specific request; the citizen is notified; the citizen submits a response; the response is attached to the complaint history and review resumes.<br>
**Alternate flows:** AI may suggest questions, but the application or authorized staff decides whether and what to request. Timeout, reminder, pause, and closure behavior require policy.<br>
**Open decisions:** Who may request information, whether AI-generated requests require approval, response deadlines, and effects on SLA clocks.

### UC-04 — Review analysis and triage

**Primary actors:** Case officer / supervisor; Complaint Analyst<br>
**Preconditions:** A complaint is registered and permitted context is available.<br>
**Main flow:** Analyst returns a structured classification, extracted facts, missing information, possible duplicate references, and uncertainty indicators. The application validates the output and presents it to an authorized reviewer or applies only explicitly approved low-risk rules.<br>
**Alternate flows:** Malformed, uncertain, conflicting, or unavailable analysis is flagged for human/manual triage; complaint data remains intact.<br>
**Open decisions:** Category taxonomy, priority/severity definitions, automation thresholds, and review policy.

### UC-05 — Route and assign a complaint

**Primary actors:** Supervisor / authorized staff; Resolution and Routing Agent<br>
**Preconditions:** Approved department, jurisdiction, and policy reference data is available or a manual review path exists.<br>
**Main flow:** Routing proposes eligible destinations and an SLA policy reference; application checks references and scope; an authorized person confirms or changes the assignment; the system records actor, reason, time, and resulting status.<br>
**Alternate flows:** Missing, stale, or conflicting mappings go to an unassigned review queue. The AI cannot create an officer, department, jurisdiction, or SLA.<br>
**Open decisions:** Destination taxonomy, automatic assignment permission, reassignment rules, and notification recipients.

### UC-06 — Work and update progress

**Primary actor:** Assigned case officer<br>
**Preconditions:** Actor is authorized for the complaint and assignment.<br>
**Main flow:** Officer reviews permitted details, records a progress action, updates an allowed status, and adds notes/evidence under the applicable visibility rules. Every state-changing action is attributable.<br>
**Alternate flows:** Concurrent updates are detected and reconciled; forbidden transitions return a stable conflict/authorization error.<br>
**Open decisions:** Internal versus citizen-visible notes, allowed transitions, evidence types, and edit/correction rules.

### UC-07 — Monitor deadline and escalate

**Primary actors:** Monitoring service / supervisor; Monitoring and Escalation Agent<br>
**Preconditions:** A versioned approved SLA and escalation policy applies.<br>
**Main flow:** System evaluates due dates; monitoring may flag upcoming risk or breach. Application validates the finding, records it, and sends or queues only permitted notifications/actions. Supervisor reviews escalations within their scope.<br>
**Alternate flows:** Missing policy data is surfaced as a configuration/review issue; notification failure is recorded and retried safely or queued for operator action.<br>
**Open decisions:** Schedule/frequency, business calendars, pause rules, escalation authority, actions, and retries.

### UC-08 — Submit and verify resolution

**Primary actors:** Case officer; authorized verifier/supervisor; citizen where policy requires<br>
**Preconditions:** Work is complete enough to submit evidence for review.<br>
**Main flow:** Officer records resolution details and evidence. A permitted verifier checks the approved criteria and either accepts closure or requests further work. The system records decision, actor, time, and rationale, then notifies the citizen as allowed.<br>
**Alternate flows:** Disputed resolution follows an approved reopen/appeal path. Failed evidence validation prevents closure.<br>
**Open decisions:** Verification authority, citizen confirmation, evidence requirements, response window, reopen and appeal rules, and separation of duties.

### UC-09 — Maintain reference data and policies

**Primary actor:** Policy administrator<br>
**Preconditions:** Actor has an explicitly granted administrative scope.<br>
**Main flow:** Administrator creates or versions department, jurisdiction, routing, SLA, or escalation data with source and effective date; change is validated, approved as required, and audited.<br>
**Alternate flows:** Invalid or overlapping rules are rejected or held for review. Historical complaint decisions retain the policy version used.<br>
**Open decisions:** Authoritative source, approval process, effective-date semantics, and retroactive change rules.

## Permission matrix (initial proposal)

Legend: **Own** = only records in the actor's permitted ownership scope; **Scoped** = assigned/department/jurisdiction scope; **Admin** = specifically granted administrative scope; **Review** = action requires separate review/approval when policy says so.

| Capability | Citizen | Officer | Supervisor | System admin | Policy admin | AI service |
|---|---|---|---|---|---|---|
| Submit complaint | Yes | If policy allows | If policy allows | Not implied | Not implied | No |
| Read complaint details | Own | Scoped | Scoped | Exceptional/support scope only | No by default | Minimum context per invocation |
| Add citizen information | Own | Scoped staff action | Scoped staff action | Not implied | No | No |
| Change assignment | No | Only if explicitly authorized | Scoped | Not implied | No | Propose only |
| Change lifecycle state | Limited citizen actions TBD | Scoped allowed transitions | Scoped allowed transitions | No by default | No | Propose only |
| Verify/close | Citizen feedback only if policy | TBD | Review if authorized | No by default | No | No |
| Manage accounts/roles | No | No | Scoped staff administration TBD | Admin | No | No |
| Manage SLA/routing policy | No | No | Propose/change TBD | No by default | Admin | Read approved data only |
| Trigger integration side effect | No | Via authorized workflow | Via authorized workflow | Via audited administration | No | Only a named allowlisted tool through application authorization |

This matrix is intentionally incomplete where policy and organizational structure are unknown. Convert it into a reviewed authorization matrix before implementing endpoints.

## Decisions needed before implementation

1. Confirm actor types, whether policy admin/verifier/auditor are distinct, and who approves the role model.
2. Approve authentication and citizen access/recovery, including anonymous-report policy.
3. Approve resource scopes and actions per lifecycle transition.
4. Define visibility classes for citizen-facing events, staff notes, attachments, and audit records.
5. Define review/separation-of-duties rules for routing, escalation, resolution, closure, and policy changes.
