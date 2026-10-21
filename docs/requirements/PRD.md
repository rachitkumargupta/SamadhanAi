# Product Requirements Document

**Status:** Target baseline from Team Kafka's supplied implementation blueprint; detailed policies require approval.<br>
**Product:** Samadhan AI<br>
**Last aligned:** 2026-10-21<br>
**Master reference:** [Implementation blueprint](../architecture/implementation-blueprint.md)

## Product vision

Samadhan AI helps citizens report civic infrastructure problems and follow them through accountable departmental work, deadline monitoring, resolution evidence, and verification. AI interprets images and complaint context and recommends actions; deterministic application workflows and authorized people control operational decisions.

## Users

- **Citizen:** submit an image-first report with optional text, provide location, track progress, provide requested information, and confirm or dispute a submitted resolution.
- **Officer:** view scoped assignments, location/image/analysis, accept or reject with a reason, record work notes/progress, submit category-appropriate resolution evidence, and inspect own workload/SLA time. Officers cannot verify on the citizen's behalf or finalize normal closure.
- **Department administrator:** manage complaints and assignments only within explicitly authorized department/jurisdiction scope; cannot bypass verification or decide disputed closures by default.
- **Independent Reviewer:** review assigned disputes and verification-overdue cases under the intended Samadhan AI policy. This is a logical role mapped to an appropriately authorized municipal authority outside the department under review, not an assumed statutory title.
- **Senior Authority:** authorize exceptional parent closure only with an explicit grant, reason, and audit record. This role does not automatically confer Independent Reviewer authority.
- **System / policy administrators:** manage only their separately granted account, operational, or policy capabilities; none implies complaint closure or dispute-review authority.
- **Three AI agents:** Complaint Analyst, Resolution & Routing, and Monitoring & Escalation. Agents are constrained system components, not user roles or authorities.

Exact role grants, real-world role mapping, scopes, and separation-of-duties details require approval. Anonymous intake and tracking are supported project policy; implementation must use a secure tracking secret separate from the public complaint ID, with rate limiting and enumeration protection.

## Target workflow

1. Citizen submits a required image, optional description, and GPS or manually selected location.
2. The API validates the request, stores complaint/media references and an initial event, and enqueues durable analysis work before any model call. Submission remains recorded if AI is unavailable.
3. The Complaint Analyst returns validated description, category, priority/severity recommendation, visible evidence, uncertainty, missing information, possible multi-department involvement, and review recommendation.
4. Resolution & Routing uses approved jurisdiction, department, officer, and policy data to recommend destinations, child-ticket splitting, and SLA policy references. Backend checks all recommendations; ambiguous cases enter human review.
5. A single-department issue creates one work ticket. A composite issue has a parent complaint and independently assigned child tickets, each with its own history and SLA. Parent progress reflects child progress.
6. A deterministic, recoverable worker checks persisted SLA deadlines in batches. It emits an idempotent breach event; Monitoring & Escalation is invoked only when a real event needs escalation reasoning.
7. Officers record progress and submit resolution evidence. “Resolved” starts a 48-hour citizen confirmation/dispute window; it does not immediately close the ticket. Notify the citizen and provide a proof card with confirm/dispute actions. At 48 hours without a response, send a reminder and keep the ticket pending. Silence is not confirmation. Disputes enter the assigned Independent Reviewer queue. If no response has arrived within seven calendar days from verification start, transition to `VERIFICATION_OVERDUE` and route to that queue under the intended project policy; silence alone never proves resolution. Process late responses before reviewer assignment under ordinary verification rules. Once review is queued/assigned, preserve the response for the reviewer; do not auto-close or cancel active review. A late dispute does not automatically reprioritize review. Serialize competing responses and review decisions and record reasoned outcomes. Calculate the deadline in the jurisdiction timezone at the same local time seven calendar dates later, persist the UTC instant and timezone context, and define daylight-saving ambiguity handling. The due boundary is `now >= deadline`; worker recovery revalidates current state.
8. Durable in-app notifications record intended delivery and outcome. Email and other channels are optional integrations and cannot undo complaint transactions.

Location and jurisdiction come from permitted device/manual coordinates and configured boundary rules, never image inference. AI suggestions never bypass server-side authorization, deterministic validation, or human review requirements.

## MVP scope

The target MVP includes image-first intake, secure media storage, location/jurisdiction capture, asynchronous analysis, human review, policy-grounded routing, parent/child work, deterministic SLA monitoring, event-triggered escalation, officer work and evidence, citizen verification/dispute, in-app notification records, scoped administration, audit, and operational recovery. The first delivery can be phased; partial implementation must be described accurately.

Duplicate detection/consolidation, heatmaps, predictive maintenance, dynamic allocation, multilingual/voice reporting, IoT, and live municipal integrations are future scope unless separately approved. Exactly three core agents are planned; no autonomous close/reject/merge and no LLM-based deadline polling.

## Quality and release outcomes

See [functional requirements](functional-requirements.md), [NFRs](non-functional-requirements.md), and [MVP release boundary](MVP-scope.md). Demonstration completion requires the image-to-verified-resolution workflow, composite tickets, deadline scale and downtime recovery, idempotent breach processing, scoped authorization, and critical acceptance tests. Passing tests and deployment evidence are required before claiming features complete.

## Open decisions

Anonymous token encoding, HMAC key storage/rotation, expiry/renewal defaults, rate-limit thresholds and recovery channel; final role grants and mapping of Independent Reviewer/Senior Authority to actual governance; approved categories and official jurisdiction/departments; image provider/storage/scanning/retention; model and data-handling terms; SLA and escalation values/calendars; reminder delivery; reviewer authority/outcomes and jurisdiction's daylight-saving ambiguity rule; scheduler/hosting guarantees; notification channel; and privacy/legal, accessibility, recovery, and capacity targets. Lost anonymous tokens have no account-style recovery without independent identity proof. Sample policies are demonstration-only and must be labelled.
