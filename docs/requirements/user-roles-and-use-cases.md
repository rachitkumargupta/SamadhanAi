# User roles and use cases

**Status:** Target actors and workflows aligned to the supplied blueprint and intended anonymous-tracking/verification policies; final grants/scopes and technical deadline semantics require approval.<br>
**Depends on:** [PRD](PRD.md)<br>
**Policy note:** Role names and capabilities below are proposals. The organization, identity model, and applicable policies have not yet been confirmed.

## Actors

| Actor | Purpose | Trust and access boundary |
|---|---|---|
| Citizen | Submit an image-first civic report, provide location/details, track progress, and confirm or dispute resolution | Access only permitted complaints. Anonymous submission/tracking is supported project policy and must use a secure high-entropy tracking secret separate from the public complaint ID. |
| Case officer | Investigate and update assigned work | May access assigned or otherwise authorized complaints and perform permitted actions within their scope. |
| Department administrator | Manage complaints and assignments only within an explicitly authorized department/jurisdiction scope | Cannot bypass citizen verification or decide a disputed closure by default. |
| Independent Reviewer | Review assigned disputed and verification-overdue cases | Logical application role, not an assumed municipal job title. Must be independent of the department whose resolution is disputed and cannot be the original officer acting as sole reviewer; may make only explicitly granted transitions. |
| Senior Authority | Authorize exceptional parent-complaint closure | Must have explicit authority, provide a reason, and create an audit record. Does not automatically hold independent-review authority. |
| System administrator | Maintain user access and operational configuration | Administrative access is privileged and must be narrowly scoped and audited; no implied complaint-closure authority. |
| Policy administrator | Maintain approved taxonomy, routing references, SLA rules, and escalation policies | Policy changes require provenance, effective dates/versioning, and an agreed approval process. Whether separate from system administrator is TBD. |
| Automated service / AI agent | Exactly three core agents propose analysis, routing, or escalation actions | Not a human identity or authority role. They use only explicitly allowed interfaces; backend authorization and policy checks remain authoritative. |

The Independent Reviewer is a logical application role. For a real deployment it must be mapped to an appropriately authorized municipal grievance officer, supervisor, or other designated authority outside the department under review; this document does not assert a statutory title or power. A real person may hold both Independent Reviewer and Senior Authority grants only when formally authorized and when the application enforces the applicable separation of duties. Policy administrators do not receive complaint-review authority by default.

## Authorization principles

- Authenticate registered actors and enforce the supported anonymous secret-based access path with the same complaint-level scope checks before enabling anonymous submissions.
- Authorize every operation on the server using both capability and resource scope. A role name alone must not grant access to every complaint.
- Keep citizen-visible status/history separate from internal notes, security events, and staff-only data.
- Treat assignment, policy changes, verification, closure, and administrative access as auditable actions.
- AI output is never a role, permission, or authorization grant. Agent proposals pass through the same application rules as other inputs.
- Define how access is removed, staff roles are changed, conflicts of interest are handled, and privileged emergency access is reviewed.

## Use cases

### UC-01 — Submit an image-first complaint

**Primary actor:** Citizen<br>
**Preconditions:** Submission policy and required fields are configured; any required identity step is complete.<br>
**Main flow:** Citizen uploads a required image, optionally adds a description, and permits device location or selects a map point. The API validates and persists the complaint, image reference, initial event, and durable analysis job before returning a reference and processing status. The Complaint Analyst runs asynchronously.<br>
**Alternate flows:** Missing text is allowed; missing location is preserved and sent to location review; invalid image is rejected safely; AI outage leaves the persisted complaint available for retry/manual review. Anonymous users receive a high-entropy tracking secret; the raw secret is not stored, access is rate-limited and non-enumerating, and regeneration revokes the prior secret. Duplicate detection is outside MVP.<br>
**Open decisions:** Secret encoding/HMAC key management and rotation, secure recovery channel, rate-limit thresholds, image controls/storage/retention, location accuracy rules, and public reference format.

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
**Main flow:** Complaint Analyst analyzes the required image and optional text, returning a grounded description, visible evidence, category and priority/severity recommendations, uncertainty, missing information, possible multi-department involvement, and review flags. Backend validates output and presents it to authorized staff.<br>
**Alternate flows:** Unusable image, malformed/uncertain result, conflicting location/text, or provider outage leaves the complaint persisted and routes to retry or manual review. Duplicate detection is outside MVP.<br>
**Open decisions:** Municipal approval of the candidate taxonomy, official priority/severity definitions and thresholds, calibrated confidence/acceptance criteria, provider/data handling, and review ownership. A provisional engineering taxonomy, evidence-scored priority rubric, categorical self-assessed confidence, and safe review triggers are implemented in the [Complaint Analyst MVP framework](../architecture/complaint-analysis-mvp-policy.md); they are not official policy.

### UC-05 — Route and assign a complaint

**Primary actors:** Supervisor / authorized staff; Resolution and Routing Agent<br>
**Preconditions:** Approved department, jurisdiction, and policy reference data is available or a manual review path exists.<br>
**Main flow:** Resolution & Routing proposes eligible departments/officers and SLA references; backend checks reference validity, jurisdiction, eligibility, and policy. A single destination gets one ticket; a composite issue gets a parent plus independent child tickets. Authorized staff confirm or adjust assignments and the system records provenance, reason, time, and state.<br>
**Alternate flows:** Missing/stale/conflicting mappings enter review; department rejection requires a reason; repeated rejection cannot loop indefinitely. AI cannot create an officer, department, jurisdiction, or SLA.<br>
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
**Main flow:** A scheduled deterministic worker scans persisted deadlines in indexed batches, safely claims and revalidates due tickets, then records idempotent breach events. Only a valid event invokes Monitoring & Escalation for a structured recommendation; backend validates authority/actions, records the outcome, and sends/queues permitted notifications. Supervisor reviews within scope.<br>
**Alternate flows:** Missing policy data is surfaced as a configuration/review issue; notification failure is recorded and retried safely or queued for operator action.<br>
**Open decisions:** Worker scheduler/claim mechanism and hosting guarantee, business calendars, pause rules, escalation authority, actions, and retry/recovery limits. Deadline comparisons remain deterministic and do not call an LLM.

### UC-08 — Submit, verify, or dispute resolution

**Primary actors:** Case officer; citizen; Independent Reviewer for disputes and approved overdue review; Senior Authority for an exceptional parent closure<br>
**Preconditions:** Work is complete enough to submit evidence for review.<br>
**Main flow:** Officer submits resolution notes and category-appropriate evidence; the backend starts the 48-hour citizen decision window and records its deadline. The citizen receives a notification and proof card/view with confirm and dispute actions. Confirmation triggers the authorized normal closure transition; a dispute enters the assigned Independent Reviewer queue. At 48 hours without a response, send a reminder and keep the complaint pending. If there is still no response within seven calendar days from verification start, route it to the reviewer under the intended project policy. The reviewer records a reasoned outcome and may close or return/reopen only when explicitly authorized. Each action is auditable and the citizen is notified through configured channels.<br>
**Alternate flows:** Silence never confirms resolution. An overdue case is not closed merely because the citizen did not respond. The original officer cannot be the sole reviewer of their own resolution. For composite work, parent progress reflects child progress; normal parent closure requires all applicable child workflows to complete. Exceptional parent closure requires an authorized Senior Authority, a reason, and an audit event; unresolved child states remain visible and unchanged.<br>
**Open decisions:** Jurisdiction daylight-saving ambiguity rule and worker operations; reminder delivery/retries; evidence by category; reviewer assignment, authority and separation; and appeal/reopen route. Late responses are recorded and processed before reviewer assignment; during review they remain visible to the reviewer and cannot auto-close/cancel review.

### UC-09 — Maintain reference data and policies

**Primary actor:** Policy administrator<br>
**Preconditions:** Actor has an explicitly granted administrative scope.<br>
**Main flow:** Administrator creates or versions department, jurisdiction, routing, SLA, or escalation data with source and effective date; change is validated, approved as required, and audited.<br>
**Alternate flows:** Invalid or overlapping rules are rejected or held for review. Historical complaint decisions retain the policy version used.<br>
**Open decisions:** Authoritative source, approval process, effective-date semantics, and retroactive change rules.

### UC-10 — Review a disputed or verification-overdue resolution

**Primary actor:** Assigned Independent Reviewer<br>
**Preconditions:** The reviewer is authorized and assigned to the case; the case is disputed or has entered the verification-overdue queue under the intended project policy. The original officer must not act as the sole reviewer of their own resolution.<br>
**Main flow:** Reviewer examines resolution evidence, complaint history, and any citizen response; records a reasoned outcome and supporting evidence. The reviewer may approve closure only if the authorization model explicitly grants that transition, or return/reopen the work for further action. A missing citizen response alone is never evidence that the issue was resolved.<br>
**Alternate flows:** Unassigned or out-of-scope reviewers are denied; conflicting or insufficient evidence remains pending or is routed to an authorized authority. Before acting, the reviewer re-reads current state and any citizen response already recorded; stale review decisions cannot override a newer response or transition. Late citizen responses remain visible to the reviewer, do not auto-close/cancel active review, and a late dispute does not automatically reprioritize it. Every decision records reviewer, time, rationale, evidence references, and resulting event/state.<br>
**Open decisions:** Appointment/mapping to the real municipal authority, case assignment, permitted outcomes, appeal route, and jurisdiction daylight-saving ambiguity rule for the seven-calendar-day handoff. Late responses are supplied to the reviewer; a late dispute does not automatically reprioritize the review.

## Permission matrix (logical roles; implementation grants require approval)

Legend: **Own** = only records in the actor's permitted ownership scope; **Scoped** = assigned/department/jurisdiction scope; **Admin** = specifically granted administrative scope; **Review** = action requires separate review/approval when policy says so.

| Capability | Citizen | Case officer | Department administrator | Independent Reviewer | Senior Authority | System administrator | Policy administrator | AI service |
|---|---|---|---|---|---|---|---|---|
| Submit complaint | Yes, subject to approved identity/access policy | No by default | No by default | No | No | No | No | No |
| View complaint | Own, with secure tracking authorization | Assigned/authorized scope | Explicit department/jurisdiction scope | Assigned review cases only | Explicitly authorized scope | No routine complaint access; separately granted support scope only | No by default | Minimum context for a bounded invocation |
| Provide requested information | Own complaint only | No; staff requests it through an authorized workflow | No by default | No | No | No | No | No |
| Submit resolution evidence | No | Yes, for assigned work | No by default | No | No by default | No | No | No |
| Initiate verification workflow | No; receives proof card and may decide | Yes; evidence submission starts the 48-hour workflow | No by default | No; handles an existing review | No | No | No | No |
| Confirm a resolution | Own complaint only; backend applies the authorized normal closure transition | No | No | Only a review outcome explicitly delegated by the authorization model | No normal citizen-verification authority | No | No | No |
| Dispute a resolution | Own complaint only | No, not on citizen's behalf | No, not on citizen's behalf | No; reviews the submitted dispute | No, not on citizen's behalf | No | No | No |
| Review disputed case | No | No; original officer cannot be sole reviewer | No by default | Assigned cases, independent of original officer/department | Only if separately granted Independent Reviewer authority | No by default | No | No |
| Review verification-overdue case | No | No | No by default | Assigned cases under the intended project policy | Only if separately granted Independent Reviewer authority | No by default | No | No |
| Normal complaint closure | Citizen confirmation initiates it; backend enforces the transition | No; submission is not closure | No bypass | Only if a specific review transition is granted | No; exceptional parent authority is separate | No | No | No |
| Exceptional parent closure | No | No | No by default | No by default | Yes, with explicit grant, reason, and audit; cannot resolve or hide children | No | No | No |
| Manage complaints/assignments | Own complaint actions only | Assigned work | Explicit department/jurisdiction scope | Assigned review actions only | Explicitly granted authority | No by default | No | Propose only; backend validates |
| Manage accounts / policy | No | No | No by default | No | No by default | Scoped account/operations administration | Scoped policy administration | Read approved references only |

Every permission is enforced in backend authorization and state-transition logic; hiding a UI control is not a security boundary. Privileged review outcomes, closure actions, role grants, and overrides record actor, timestamp, rationale, and relevant evidence/policy references. This logical matrix does not grant statutory powers; map roles to the real authority and approve the actual grant matrix before implementation.

## Decisions needed before implementation

1. Confirm actor types, whether policy admin/verifier/auditor are distinct, and who approves the role model.
2. Select the authentication mechanism and approve citizen access/recovery details for the supported anonymous-tracking flow; the policy to support anonymous reporting is established.
3. Approve resource scopes and actions per lifecycle transition.
4. Define visibility classes for citizen-facing events, staff notes, attachments, and audit records.
5. Define review/separation-of-duties rules for routing, escalation, resolution, closure, and policy changes.
