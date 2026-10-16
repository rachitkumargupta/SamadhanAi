# Functional requirements

**Status:** Draft for Team Kafka review<br>
**Source:** [PRD](PRD.md) and [user roles and use cases](user-roles-and-use-cases.md)<br>
**Version:** 0.1<br>

These requirements describe intended system behavior. They are not evidence of implementation. “Must” indicates a proposed MVP requirement; policy-specific behavior remains subject to approval. Priority: **Must** = required for the first end-to-end MVP; **Should** = valuable but can follow the core workflow; **TBD** = priority depends on team/policy decision.

## 1. Identity and access control

| ID | Priority | Requirement | Acceptance criteria | Use cases |
|---|---|---|---|---|
| FR-IAM-01 | Must | The system must identify the acting user or explicitly represent an allowed anonymous submission. | Requests requiring identity cannot proceed without an approved identity context. Anonymous access is rejected or handled only according to the approved policy. | UC-01, UC-02 |
| FR-IAM-02 | Must | The system must enforce role, action, and complaint-level authorization on every protected operation. | A user outside the permitted scope cannot read, modify, assign, or transition a complaint by changing an ID or bypassing the UI. Denials do not disclose protected record details. | UC-02–UC-09 |
| FR-IAM-03 | Must | Administrative and policy-management permissions must be separately grantable and auditable. | Role or permission grants and revocations identify actor, target, time, and reason; exact role separation is approved before release. | UC-09 |
| FR-IAM-04 | Must | The system must expose citizen, staff, and administrative representations according to their approved visibility rules. | Citizen responses omit staff-only notes and internal audit/security data; automated contract/access checks demonstrate permitted and denied cases. | UC-02, UC-06, UC-08 |

## 2. Complaint intake and access

| ID | Priority | Requirement | Acceptance criteria | Use cases |
|---|---|---|---|---|
| FR-CMP-01 | Must | The system must validate a complaint submission against the configured schema and policy. | Valid input creates a complaint; invalid input returns safe field-level errors and creates no partial complaint record. Required fields are team-approved. | UC-01 |
| FR-CMP-02 | Must | The system must assign a unique, stable complaint reference on successful registration. | A successful submission returns a reference usable in authorized tracking; reference generation avoids unintended collisions and does not reveal sequential internal IDs. Format is TBD. | UC-01, UC-02 |
| FR-CMP-03 | Must | Registration must persist the complaint and its initial lifecycle event atomically. | If either record cannot be committed, neither is reported as successfully registered; retries follow the agreed idempotency policy. | UC-01 |
| FR-CMP-04 | Should | The system should accept optional evidence attachments subject to approved upload and retention rules. | Disallowed or oversized files are rejected safely; access to accepted evidence follows complaint authorization; storage/provider failure is visible and does not silently discard data. Limits and scan controls are TBD. | UC-01, UC-03, UC-06, UC-08 |
| FR-CMP-05 | Must | The system must allow an authorized citizen or staff member to retrieve the current complaint view. | Response includes only fields visible to the actor and indicates current status; missing and unauthorized records use non-disclosing behavior. | UC-02 |
| FR-CMP-06 | Must | The system must provide authorized complaint list/search views with bounded scope and pagination. | Citizen results are limited to permitted complaints; staff results are limited to assigned/department/jurisdiction scope; result size is bounded. Filter and pagination contract is TBD. | UC-02, UC-05, UC-07 |
| FR-CMP-07 | Must | The system must record complaint events for material state changes and actions. | Each event records actor or system identity, action, timestamp, and relevant reason/reference; visibility is filtered for citizens. Correction and retention policy is TBD. | UC-01–UC-09 |

## 3. Information requests and analysis

| ID | Priority | Requirement | Acceptance criteria | Use cases |
|---|---|---|---|---|
| FR-ANL-01 | Must | The system must support requesting and recording missing information. | An authorized request identifies what information is needed; citizen response is linked to the complaint and recorded in history; policy determines reminders/timeouts. | UC-03, UC-04 |
| FR-ANL-02 | Must | Complaint analysis must return a versioned structured result for the agreed taxonomy and fields. | Result is schema-validated before use; invalid or incomplete result is rejected and recorded as a controlled failure/review case. Fields and taxonomy are TBD. | UC-04 |
| FR-ANL-03 | Must | Analysis must distinguish extracted facts from inferred suggestions and identify uncertainty. | Reviewer can identify suggested category/priority/severity and any uncertainty/evidence; unsupported values are not silently treated as facts. Confidence semantics are TBD. | UC-04 |
| FR-ANL-04 | Must | Analysis may identify missing information and possible duplicates, but must not independently merge, reject, or close complaints. | Any proposed follow-up or duplicate relationship passes through approved application rules and, when required, human review. Duplicate consolidation is out of MVP unless explicitly approved. | UC-03, UC-04 |
| FR-ANL-05 | Must | Analysis failure, timeout, or uncertain output must preserve complaint data and allow manual handling. | Complaint remains in a defined reviewable state; failure is traceable; no unsupported classification or routing is committed. | UC-04 |

## 4. Reference data, routing, and assignment

| ID | Priority | Requirement | Acceptance criteria | Use cases |
|---|---|---|---|---|
| FR-ROU-01 | Must | Routing decisions must refer only to approved department, jurisdiction, team/officer, and policy records. | Every accepted route resolves to current authorized reference data; nonexistent, stale, or conflicting values are rejected or sent to review. | UC-05, UC-09 |
| FR-ROU-02 | Must | Routing must provide a review/unassigned path when no valid mapping exists. | Complaint remains visible to authorized triage staff and is not assigned to an invented destination. | UC-05 |
| FR-ROU-03 | Must | An authorized person or explicitly approved deterministic rule must confirm an assignment. | Assignment records source/actor, target, time, and reason; agent output alone cannot create an assignment. | UC-05 |
| FR-ROU-04 | Must | Reassignment must preserve assignment history and enforce actor scope. | Previous and new assignment are visible to permitted staff with actor, timestamp, and reason; unauthorized reassignment is denied. | UC-05, UC-06 |
| FR-ROU-05 | Must | Reference data and policy changes must have provenance and effective/version information. | Authorized changes are attributable; historical decisions can identify the applicable reference/policy version; retroactive effects follow an approved rule. | UC-09 |

## 5. Lifecycle, SLA, and escalation

| ID | Priority | Requirement | Acceptance criteria | Use cases |
|---|---|---|---|---|
| FR-LCY-01 | Must | The system must enforce an approved complaint state machine. | Only defined transitions with satisfied preconditions and actor permissions succeed; invalid transitions return a stable conflict/validation error. State names and transition table are pending approval. | UC-05–UC-08 |
| FR-LCY-02 | Must | The system must record progress actions and status changes with actor and time. | Authorized staff can record permitted progress; each material update creates attributable history; concurrency conflicts are detected rather than silently overwriting changes. | UC-06 |
| FR-SLA-01 | Must | Due dates must be calculated from an approved, versioned SLA rule. | Calculation identifies the rule/version and input timestamps; missing or ambiguous policy is surfaced for review rather than guessed. Values and calendar semantics are TBD. | UC-05, UC-07 |
| FR-SLA-02 | Must | The system must identify upcoming deadlines and breaches according to approved monitoring rules. | Evaluation records the complaint, policy version, evaluation time, and finding; repeat evaluations do not create uncontrolled duplicate actions. Schedule/frequency is TBD. | UC-07 |
| FR-ESC-01 | Must | Escalation actions must be limited to approved policy and authorized actors. | Monitoring can recommend an action; the application verifies the rule and authority before acting; all findings and decisions are traceable. | UC-07 |
| FR-ESC-02 | Must | Failed escalation or notification delivery must be visible and safely recoverable. | Attempt and result are recorded; retries are bounded/idempotent or surfaced for operator action; complaint state is not falsely represented as notified. | UC-07 |

## 6. Resolution and closure

| ID | Priority | Requirement | Acceptance criteria | Use cases |
|---|---|---|---|---|
| FR-CLS-01 | Must | Authorized staff must be able to submit resolution details and evidence for review. | Submission records actor/time and remains distinguishable from verified closure. Required evidence is policy-defined. | UC-08 |
| FR-CLS-02 | Must | The system must prevent closure until the approved verification policy is satisfied. | Missing verification/evidence or unauthorized actor prevents closure; accepted or rejected verification records actor, time, outcome, and rationale. | UC-08 |
| FR-CLS-03 | Must | The system must support the approved disputed-resolution, reopen, or appeal path. | A citizen dispute or reviewer rejection follows an explicitly configured route and creates an auditable event; exact path is TBD. | UC-08 |

## 7. Notifications, administration, and audit

| ID | Priority | Requirement | Acceptance criteria | Use cases |
|---|---|---|---|---|
| FR-NOT-01 | Must | The system must create a traceable notification record for configured complaint events. | Recipient, channel, event/template reference, attempt time, and outcome are recorded; content follows channel privacy rules. Channels and templates are TBD. | UC-01, UC-03, UC-05, UC-07, UC-08 |
| FR-NOT-02 | Must | Notification delivery must be retry-safe and must not block or corrupt the authoritative complaint transaction. | Delivery failure is recorded separately from complaint state; retry does not create unintended duplicate messages where idempotency is supported. | UC-07, UC-08 |
| FR-ADM-01 | Must | Authorized administrators must be able to inspect operational queues and relevant complaint history within scope. | Views enforce scope and visibility; sensitive fields are minimized; all privileged access follows approved audit rules. | UC-05–UC-09 |
| FR-ADM-02 | Must | Authorized policy administrators must manage approved reference data through validated changes. | Invalid or conflicting configuration is rejected or held for review; changes have provenance, version/effective date, and an audit record. | UC-09 |
| FR-AUD-01 | Must | The system must maintain protected audit history for privileged actions and material lifecycle decisions. | Entries identify actor/system, action, target, time, and reason/reference; ordinary users and agents cannot rewrite history. Retention and export policy is TBD. | UC-01–UC-09 |

## 8. Requirements still requiring policy decisions

The following are deliberate TBDs, not implementation gaps to resolve by guesswork:

- Required complaint fields, taxonomy, priority/severity definitions, and any confidence thresholds.
- Anonymous reporting, authentication, citizen access recovery, and public complaint references.
- Complaint states/transitions, visibility of events and notes, corrections, withdrawal, rejection, reopen, and appeal.
- Department/jurisdiction data source, route eligibility, assignment automation, and policy ownership.
- SLA values, clock start/pause/resume, working calendars/timezones, breach stages, and escalation actions.
- Verification authority, resolution evidence, citizen confirmation, and separation of duties.
- Attachment formats, limits, storage, malware scanning, retention, and access.
- Notification channels, sensitive-content rules, delivery retry strategy, and consent/preferences.
- Audit retention, personal-data retention/deletion, and applicable legal/institutional obligations.

## Traceability and change control

Each requirement ID should remain stable when wording changes; retire IDs with a note rather than reusing them. Before implementation, product/policy owners should approve each Must requirement and its TBD dependencies. During development, link tests and API/data design to requirement IDs in pull requests or the team's chosen issue tracker. Update this document whenever the approved workflow or acceptance criteria change.
