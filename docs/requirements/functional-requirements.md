# Functional requirements

**Status:** Target requirements aligned to the supplied project blueprint; operational policy details remain pending approval.<br>
**Source:** [PRD](PRD.md), [roles and use cases](user-roles-and-use-cases.md), and [master blueprint](../architecture/implementation-blueprint.md)<br>
**Version:** 0.2<br>

These requirements describe intended behavior and are not evidence of implementation. **Must** means required for the first end-to-end MVP. Blueprint-mandated behavior (including required image intake, exactly three core agents, the 48-hour citizen decision window, reminder with the complaint kept pending after no response, and no closure by silence) is the baseline; changing it requires an explicit approved specification change. Policy-specific values and operational details remain subject to approval. **Should** can follow the core workflow; **TBD** means priority depends on a team/policy decision.

## 1. Identity and access control

| ID | Priority | Requirement | Acceptance criteria | Use cases |
|---|---|---|---|---|
| FR-IAM-01 | Must | The system must identify the acting user or explicitly support an anonymous submission with complaint-scoped tracking access. | Registered requests use the authenticated actor. Anonymous submission issues a high-entropy tracking secret, stores only a protected verifier, rate-limits access and prevents complaint enumeration; secret revocation/regeneration invalidates prior access. Anonymous actions are not attributed to a fictitious registered user. | UC-01, UC-02 |
| FR-IAM-02 | Must | The system must enforce role, action, and complaint-level authorization on every protected operation. | A user outside the permitted scope cannot read, modify, assign, or transition a complaint by changing an ID or bypassing the UI. Denials do not disclose protected record details. | UC-02–UC-10 |
| FR-IAM-03 | Must | Administrative, policy-management, Independent Reviewer, and Senior Authority permissions must be separately grantable and auditable. | Role or permission grants and revocations identify actor, target, time, and reason; reviewer separation from the original officer and any dual-role Senior Authority grants are explicitly approved. | UC-09, UC-10 |
| FR-IAM-04 | Must | The system must expose citizen, staff, and administrative representations according to their approved visibility rules. | Citizen responses omit staff-only notes and internal audit/security data; automated contract/access checks demonstrate permitted and denied cases. | UC-02, UC-06, UC-08 |

## 2. Complaint intake and access

| ID | Priority | Requirement | Acceptance criteria | Use cases |
|---|---|---|---|---|
| FR-CMP-01 | Must | The system must accept an image as required complaint evidence and a written description as optional context. | Upload validation checks decoded content, configured type/size/dimensions, and approved safety controls; a missing text description is permitted. JPEG, PNG and WebP are the blueprint's initial recommended formats, subject to implementation validation. | UC-01 |
| FR-CMP-02 | Must | The system must assign a unique, stable complaint reference on successful registration. | A successful submission returns a reference usable in authorized tracking; reference generation avoids unintended collisions and does not reveal sequential internal IDs. Format is TBD. | UC-01, UC-02 |
| FR-CMP-03 | Must | Registration must persist the complaint and its initial lifecycle event atomically. | If either record cannot be committed, neither is reported as successfully registered; retries follow the agreed idempotency policy. | UC-01 |
| FR-CMP-04 | Must | The system must privately store the required complaint image and any later resolution evidence. | Store object references rather than public URLs; normalize safely, strip unnecessary EXIF, enforce access-controlled retrieval, and apply approved scanning, retention, and deletion controls. File-size and pixel-dimension limits plus storage provider are TBD. | UC-01, UC-08 |
| FR-CMP-08 | Must | The system must capture location from explicit device permission or a manual map selection. | Record coordinates and available accuracy, time, and source; never fabricate coordinates. If location is unavailable, preserve the complaint and route it to location review. Resolve jurisdiction from configured boundaries/rules, not image interpretation. | UC-01, UC-05 |
| FR-CMP-09 | Must | The system must persist the complaint before scheduling asynchronous AI analysis. | Complaint, initial event, media references, and durable analysis-job intent are recorded consistently; AI/provider failure does not lose the report. Submission returns an initial processing status. | UC-01, UC-04 |
| FR-CMP-05 | Must | The system must allow an authorized citizen or staff member to retrieve the current complaint view. | Citizen projection includes public status, assigned department/progress where permitted, parent/child progress, and permitted resolution evidence; it excludes staff-only notes/audit details. Missing and unauthorized records use non-disclosing behavior. | UC-02 |
| FR-CMP-06 | Must | The system must provide authorized complaint list/search views with bounded scope and pagination. | Citizen results are limited to permitted complaints; staff results are limited to assigned/department/jurisdiction scope; result size is bounded. Filter and pagination contract is TBD. | UC-02, UC-05, UC-07 |
| FR-CMP-07 | Must | The system must record complaint events for material state changes and actions. | Each event records actor or system identity, action, timestamp, and relevant reason/reference; visibility is filtered for citizens. Correction and retention policy is TBD. | UC-01–UC-10 |

## 3. Information requests and analysis

| ID | Priority | Requirement | Acceptance criteria | Use cases |
|---|---|---|---|---|
| FR-ANL-01 | Must | The system must support requesting and recording missing information. | An authorized request identifies what information is needed; citizen response is linked to the complaint and recorded in history; policy determines reminders/timeouts. | UC-03, UC-04 |
| FR-ANL-02 | Must | The Complaint Analyst must return a versioned structured result using the complaint image, optional description, and permitted location metadata. | Result includes visible evidence, generated description when needed, category and severity/priority recommendations, uncertainty, missing-information flags, possible multi-department need, and review recommendation; schema and references are validated. Taxonomy remains TBD. | UC-04 |
| FR-ANL-03 | Must | Analysis must distinguish extracted facts from inferred suggestions and identify uncertainty. | Reviewer can identify suggested category/priority/severity and any uncertainty/evidence; unsupported values are not silently treated as facts. Confidence semantics are TBD. | UC-04 |
| FR-ANL-04 | Must | Analysis must not independently reject, assign, merge, close, or perform actions. | Duplicate detection/consolidation is outside MVP; all agent results are proposals validated by backend rules and reviewed where required. | UC-04 |
| FR-ANL-05 | Must | Analysis failure, timeout, or uncertain output must preserve complaint data and allow manual handling. | Complaint remains in a defined reviewable state; failure is traceable; no unsupported classification or routing is committed. | UC-04 |
| FR-ANL-06 | Must | The system must use a configurable civic issue taxonomy and deterministic rules to validate or adjust model priority recommendations. | Initial category candidates are roads/potholes, garbage/sanitation, drainage/sewage, water/leakage, streetlights/electrical infrastructure, damaged public infrastructure, and other/uncertain. Safety-critical/emergency cases follow explicit rules and must not depend only on model judgment. Taxonomy/rules require policy approval. | UC-04, UC-05 |

## 4. Reference data, routing, and assignment

| ID | Priority | Requirement | Acceptance criteria | Use cases |
|---|---|---|---|---|
| FR-ROU-01 | Must | Routing decisions must refer only to approved department, jurisdiction, team/officer, and policy records. | Every accepted route resolves to current authorized reference data; nonexistent, stale, or conflicting values are rejected or sent to review. | UC-05, UC-09 |
| FR-ROU-02 | Must | Routing must provide a review/unassigned path when no valid mapping exists. | Complaint remains visible to authorized triage staff and is not assigned to an invented destination. | UC-05 |
| FR-ROU-03 | Must | Backend validation must check any proposed assignment against active department, officer, jurisdiction, workload, and policy constraints before applying it. | Clear-case automation is permitted only when explicitly configured; uncertain/conflicting cases enter human review. Assignment provenance, actor/source, target, time, and reason are recorded. | UC-05 |
| FR-ROU-04 | Must | Reassignment must preserve assignment history and enforce actor scope. | Previous and new assignment are visible to permitted staff with actor, timestamp, and reason; unauthorized reassignment is denied. | UC-05, UC-06 |
| FR-ROU-05 | Must | Reference data and policy changes must have provenance and effective/version information. | Authorized changes are attributable; historical decisions can identify the applicable reference/policy version; retroactive effects follow an approved rule. | UC-09 |
| FR-ROU-06 | Must | A composite complaint must support a parent record and multiple department-specific child tickets. | Each child has independent assignment, status history, evidence, escalation history, and SLA; parent progress derives from its children. Rejections require a reason; repeated conflict/bouncing enters human review. | UC-05, UC-06 |
| FR-ROU-07 | Must | An officer rejecting an assignment must provide a reason. | Record reason and department/jurisdiction context; controlled reassignment preserves history; repeated rejection/conflict enters human review rather than an uncontrolled loop. | UC-05 |

## 5. Lifecycle, SLA, and escalation

| ID | Priority | Requirement | Acceptance criteria | Use cases |
|---|---|---|---|---|
| FR-LCY-01 | Must | The system must enforce an approved complaint state machine. | Only defined transitions with satisfied preconditions and actor permissions succeed; invalid transitions return a stable conflict/validation error. State names and transition table are pending approval. | UC-05–UC-08 |
| FR-LCY-02 | Must | The system must record progress actions and status changes with actor and time. | Authorized staff can record permitted progress; each material update creates attributable history; concurrency conflicts are detected rather than silently overwriting changes. | UC-06 |
| FR-SLA-01 | Must | Due dates must be calculated from an approved, versioned SLA rule. | Calculation identifies the rule/version and input timestamps; missing or ambiguous policy is surfaced for review rather than guessed. Values and calendar semantics are TBD. | UC-05, UC-07 |
| FR-SLA-02 | Must | A deterministic scheduled worker must identify warnings and breaches from persisted SLA deadlines in bounded batches. | Worker claims and revalidates due records, emits durable idempotent events, and recovers overdue work after downtime; thousands of active tickets do not trigger per-ticket LLM polling. Scheduler/claim mechanism is TBD. | UC-07 |
| FR-SLA-03 | Must | Each ticket's SLA lifecycle must be stored separately from its complaint status. | Support `NOT_STARTED`, `ACTIVE`, `WARNING_SENT`, `BREACHED`, `PAUSED` only under explicit policy, `COMPLETED`, and `CANCELLED` only when validly superseded/invalidated; persist policy version and deadline per child. | UC-05, UC-07 |
| FR-ESC-01 | Must | The Monitoring & Escalation Agent must be invoked by a valid breach/escalation event, not continuous polling. | It returns a structured summary and next-authority recommendation; backend validates hierarchy/authority, persists outcome, and sends/queues only permitted actions. | UC-07 |
| FR-ESC-02 | Must | Failed escalation or notification delivery must be visible and safely recoverable. | Attempt and result are recorded; retries are bounded/idempotent or surfaced for operator action; complaint state is not falsely represented as notified. | UC-07 |

## 6. Resolution and closure

| ID | Priority | Requirement | Acceptance criteria | Use cases |
|---|---|---|---|---|
| FR-CLS-01 | Must | Authorized staff must be able to submit resolution details and evidence for review. | Submission records actor/time and remains distinguishable from verified closure. Required evidence is policy-defined. | UC-08 |
| FR-CLS-02 | Must | Officer resolution must enter pending citizen verification and must not close the complaint immediately. | Persist the 48-hour decision deadline; notify the citizen and present permitted evidence in a proof view with confirm/dispute actions. Confirmation initiates authorized normal closure. At 48 hours without response, send a reminder and keep the complaint pending. Silence never counts as confirmation. | UC-08 |
| FR-CLS-03 | Must | A citizen dispute must enter a separately authorized Independent Reviewer queue. | Department administrators and the original officer cannot decide the dispute by default; the reviewer records a reasoned, auditable outcome and may perform only explicitly authorized transitions. The original officer cannot be the sole reviewer of their own resolution. | UC-08, UC-10 |
| FR-CLS-04 | Must | Parent completion must reflect child completion and verification. | Normal parent closure requires all applicable child workflows to complete; exceptional parent closure requires an authorized Senior Authority, reason, and audit event, and cannot mark unresolved children complete or conceal them. Independent-review authority is not implied. | UC-08 |
| FR-CLS-05 | Must | If no citizen response has arrived by the seven-calendar-day deadline after verification starts, the child must enter `VERIFICATION_OVERDUE` and the Independent Reviewer queue under the intended Samadhan AI policy. | At 48 elapsed hours, send the required reminder and keep the case pending. At the seven-day deadline, create one idempotent reviewer case and revalidate current state. Process a late response received before reviewer assignment through ordinary verification rules. Once review is queued/assigned, preserve responses for the assigned reviewer; never auto-close or cancel active review. A late dispute does not automatically reprioritize review; the reviewer considers it as new input. Serialize concurrent responses, assignment/reassignment, and reviewer decisions; record each review outcome, actor, time, reason, and authorized transition. Reviewer may close only if explicitly authorized and evidence supports it; otherwise use an authorized return/reopen/further-action outcome. Silence alone never justifies closure. Derive the deadline in the complaint jurisdiction timezone, preserve timezone context, persist the due instant as UTC, treat `now >= deadline` as due, define daylight-saving ambiguity handling, and recover missed work after downtime. | UC-08, UC-10 |

## 7. Notifications, administration, and audit

| ID | Priority | Requirement | Acceptance criteria | Use cases |
|---|---|---|---|---|
| FR-NOT-01 | Must | The system must create durable in-app notification records for configured complaint events. | Cover receipt, analysis completion/review, assignment/reassignment, information requests, progress, SLA warnings/escalations, resolution submission, the 48-hour verification reminder, citizen decision, reviewer assignment/outcome, and overdue-review handoff. Record recipient, event/template and each delivery attempt/outcome; email is an optional adapter. | UC-01, UC-03, UC-05, UC-07, UC-08, UC-10 |
| FR-NOT-02 | Must | Notification delivery must be retry-safe and must not block or corrupt the authoritative complaint transaction. | Delivery failure is recorded separately from complaint state; retry does not create unintended duplicate messages where idempotency is supported. | UC-07, UC-08 |
| FR-ADM-01 | Must | Authorized administrators must be able to inspect operational queues and relevant complaint history within scope. | Views enforce scope and visibility; sensitive fields are minimized; all privileged access follows approved audit rules. Independent-review access is separately granted, not inherited from administrator status. | UC-05–UC-10 |
| FR-ADM-02 | Must | Authorized policy administrators must manage approved reference data through validated changes. | Invalid or conflicting configuration is rejected or held for review; changes have provenance, version/effective date, and an audit record. | UC-09 |
| FR-ADM-03 | Should | Authorized staff/admins should see scoped workload and service-performance indicators. | Officer, department, and ward summaries use authorized aggregate data and include relevant overdue/SLA, assignment, rejection, and resolution measures; no department admin sees unrestricted cross-department complaint details. | UC-07, UC-09 |
| FR-ADM-04 | Must | Authorized administrators must be able to inspect failed processing jobs, overdue complaints, system health, and audit history within scope. | Queue views expose recoverable status and safe error metadata without leaking credentials, model prompts, or unrestricted complaint data. | UC-07, UC-09 |
| FR-AUD-01 | Must | The system must maintain protected audit history for privileged actions and material lifecycle decisions. | Entries identify actor/system, action, target, time, and reason/reference; ordinary users and agents cannot rewrite history. Retention and export policy is TBD. | UC-01–UC-10 |

## 8. Requirements still requiring policy decisions

The following are deliberate TBDs, not implementation gaps to resolve by guesswork:

- Required complaint fields, taxonomy, priority/severity definitions, and any confidence thresholds.
- Anonymous token encoding/key management/rotation, expiry and renewal defaults, rate-limit thresholds, recovery channel (lost tokens have no account-style recovery without independent identity proof), staff authentication, and public complaint-reference format.
- State/enum names, transition implementation, visibility of events and notes, corrections, withdrawal, rejection, reopen, and appeal. Citizen confirm/dispute actions, the 48-hour reminder, and no-closure-by-silence are fixed requirements.
- Department/jurisdiction data source, route eligibility, assignment automation, and policy ownership.
- SLA values, clock start/pause/resume, working calendars/timezones, breach stages, and escalation actions.
- Mapping the logical Independent Reviewer and Senior Authority roles to the actual organization; evidence-by-category and separation-of-duties details.
- Image formats/limits, object storage, scanning/normalization, retention/deletion, and access.
- Jurisdiction timezone source and daylight-saving ambiguity rule for the seven-day verification-overdue handoff; reminder delivery/retries and reviewer authority/assignment/outcome workflow. Late-response handling is specified in FR-CLS-05; confirm real-world reviewer mapping and transition grants before implementation.
- Durable job scheduler/worker deployment guarantees, claim/retry behavior, and downtime recovery.
- Notification channels, sensitive-content rules, delivery retry strategy, and consent/preferences.
- Audit retention, personal-data retention/deletion, and applicable legal/institutional obligations.

## Traceability and change control

Each requirement ID should remain stable when wording changes; retire IDs with a note rather than reusing them. Before implementation, product/policy owners should approve each Must requirement and its genuine TBD dependencies. FR-CLS-05's seven-calendar-day threshold and late-response handling are intended project policy; the jurisdiction timezone source, daylight-saving ambiguity rule, reviewer authority/mapping, and operational recovery details must be confirmed before implementation. During development, link tests and API/data design to requirement IDs in pull requests or the team's chosen issue tracker. Update this document whenever the approved workflow or acceptance criteria change.
