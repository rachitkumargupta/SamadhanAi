# Product Requirements Document

**Status:** Draft for Team Kafka review<br>
**Product:** Samadhan AI<br>
**Date:** 2026-10-16

For the proposed actors, permission boundaries, and detailed use-case flows, see [user roles and use cases](user-roles-and-use-cases.md).
The traceable MVP behavior requirements are in [functional requirements](functional-requirements.md).
Quality and operational requirements are detailed in [non-functional requirements](non-functional-requirements.md); capacity and service-level targets remain pending team input.
The proposed release boundary and gates are in [MVP scope](MVP-scope.md).

## Problem

Citizens may lack a transparent way to submit civic complaints, learn where they were routed, understand progress and deadlines, and know whether a reported issue was actually resolved. Civic staff may lack a consistent workflow for intake, triage, assignment, monitoring, and auditable closure. The intended system supports this lifecycle while preserving authorized human control.

## Users and responsibilities

- **Citizen:** submit a complaint, provide requested details, track its status, receive updates, and provide feedback or challenge a proposed resolution under policy.
- **Officer / case handler:** review assigned complaints, request information, record actions, update progress, and submit resolution evidence.
- **Department supervisor:** oversee a department queue, reassign work where authorized, and respond to delay/escalation prompts.
- **Administrator / policy steward:** manage approved users, roles, departments, jurisdiction mappings, SLA policies, and operational configuration. Exact administrative boundaries are pending.
- **Support / auditor (optional role):** inspect permitted history and help investigate access or process issues. Whether this is a distinct role is pending.

## Product goals

1. Give a complaint a stable identifier and understandable status.
2. Route work using approved department, jurisdiction, and policy data.
3. Make important decisions, assignments, transitions, and notifications traceable.
4. Surface missing information and deadlines without presenting AI output as authoritative.
5. Support resolution evidence and a team-approved closure verification policy.

## Core workflow

1. Citizen submits complaint and optional attachment/location details.
2. System validates and registers it, returns an identifier, and records an audit event.
3. Analyst proposes structured classification and flags missing details or possible duplicates.
4. Authorized staff/system rules decide whether to ask for more information or continue.
5. Routing uses approved mappings to propose a department/team and applicable SLA; uncertain or unmapped cases enter human review.
6. Authorized personnel accept or change assignment; citizen receives a status update as appropriate.
7. Monitoring evaluates due dates and permitted escalation rules, recording alerts/actions.
8. Officer records work and submits resolution evidence.
9. Required reviewer or verification policy determines closure; citizen is notified and the record remains auditable.

Detailed states, transition permissions, SLA clocks, and verification evidence are **pending team and policy agreement**.

## Functional requirements (proposed)

- **FR-01 Intake:** accept complaint text and configured structured fields; validate and acknowledge with a unique, non-guessable public reference.
- **FR-02 Attachments:** support optional evidence subject to file type/size, malware scanning, access, and retention policy (limits TBD).
- **FR-03 Identity and roles:** authenticate applicable users and enforce server-side role and resource-level authorization.
- **FR-04 Tracking:** expose only permitted complaint details and status history to a citizen and authorized staff.
- **FR-05 Analysis:** produce schema-validated category/severity/priority suggestions, missing-information prompts, rationale/provenance, and confidence/uncertainty handling.
- **FR-06 Routing:** use maintained department, jurisdiction, and policy data; never invent a destination or SLA. Support unassigned/review queues.
- **FR-07 Assignment:** record assignment, actor, time, and reason; enforce authorized changes.
- **FR-08 SLA and monitoring:** calculate due dates from approved rules and recorded timestamps; detect upcoming or breached deadlines.
- **FR-09 Notifications:** record delivery attempts and outcomes; avoid exposing sensitive content through insecure channels.
- **FR-10 Resolution and closure:** record actions/evidence and enforce the approved verification and closure transition policy.
- **FR-11 Audit:** preserve attributable state changes and privileged actions; define correction and retention policies.
- **FR-12 Administration:** provide authorized maintenance of reference data and policy, with audit history.

## Non-functional requirements (initial targets pending review)

- **Security/privacy:** least privilege, validated inputs, encrypted transport, protected credentials, limited personal data, documented retention, and access auditing.
- **Reliability:** transactional complaint creation and transitions; retry-safe external side effects; clear degraded-mode behavior.
- **Usability/accessibility:** plain-language status and accessible citizen/staff experiences; target standard and supported languages TBD.
- **Performance/capacity:** expected users, submission volume, attachment sizes, and response-time objectives are TBD; establish measurable targets before release.
- **Observability:** structured operational logs and metrics with correlation IDs while excluding unnecessary complaint text, credentials, and personal data.
- **Maintainability:** modular boundaries, migration-managed schema changes, automated checks, and documented API contracts.
- **AI quality:** bounded outputs, validation, evaluation on representative approved data, human review thresholds, and a non-AI fallback path.

## MVP scope

Include role-aware access, complaint intake/IDs, tracking, staff and department records, an auditable lifecycle, manual or policy-backed classification/routing, missing-information handling, assignments, configurable SLA rules, notification records, escalation records, resolution evidence, closure controls, and administrative visibility.

The first usable milestone should complete the complaint lifecycle end to end. AI can initially make bounded suggestions behind explicit interfaces; core recordkeeping and human workflows must remain usable when AI is unavailable.

## Out of scope for MVP (unless re-approved)

Duplicate consolidation, geographical heatmaps, predictive maintenance, dynamic resource/SLA allocation, multilingual/voice reporting, IoT, city-wide analytics, and live government/municipal system integrations. Availability of any such integration is unverified.

## Acceptance criteria for MVP (draft)

- A permitted citizen can submit a valid complaint and receive a reference; invalid input is rejected with a safe actionable error.
- A citizen can see only their permitted complaint information; unauthorized users cannot read or change it.
- Authorized staff can review, assign, update, and record resolution with attributable history.
- Routing and SLA use configured approved data, or explicitly enter a review/unassigned path when data is missing.
- Due-date monitoring and notification outcomes are traceable; duplicate requests do not create unintended duplicate effects where idempotency is required.
- Closure cannot occur without satisfying the team-approved verification policy.
- AI failure or invalid output does not corrupt the complaint or bypass authorization; a human/manual path remains available.
- Requirements have tests and operational/documentation checks agreed for the release.

## Assumptions and open questions

- The supplied brief is the only inspected product reference; the presentation was not found in the searched locations.
- Target city/authority, jurisdiction boundaries, department taxonomy, policies, SLA values, identity proofing needs, notification channels, retention rules, and legal obligations are unknown.
- Decide whether anonymous reports are allowed and how citizens authenticate or recover access.
- Decide if/when AI suggestions require mandatory approval and what confidence/uncertainty behavior is acceptable.
- Define complaint statuses, reopen/appeal behavior, closure verification evidence, and escalation authority.
- Define expected scale, accessibility/language targets, hosting, backup, and availability objectives.
- Confirm technology versions, ORM/migration tool, LLM provider, frontend setup, testing stack, and deployment platform in ADR review.
