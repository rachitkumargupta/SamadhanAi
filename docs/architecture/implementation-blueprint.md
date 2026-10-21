# Master implementation blueprint

**Status:** Team Kafka implementation baseline; policy and deployment decisions listed below remain subject to approval.<br>
**Source:** Supplied “Samadhan AI — Complete Project Specification & Implementation Blueprint” (2026-10-21).<br>
**Purpose:** This page records the cross-document decisions that all requirements and architecture documents must follow. It describes the target, not implemented functionality.

## Product and architecture direction

- Build an AI-assisted civic complaint workflow. Application code remains authoritative for identity, permissions, validation, assignments, state changes, SLA calculations, event handling, notifications, and audit records.
- Image-first intake is the target: a complaint includes an image; a written description is optional and may be generated from visible evidence. JPEG, PNG, and WebP are the initial recommended formats, with configured size/pixel limits, decoded-content validation, safe normalization, and EXIF handling. Decide whether to preserve originals or normalized copies under the evidence policy. Persist the complaint and a durable analysis job before calling an AI provider.
- Capture location with explicit device permission or a manually selected map point. Never invent coordinates. Resolve jurisdiction from configured boundaries and rules, not from image interpretation.
- Support a parent complaint with independently assigned child tickets when multiple departments must act. Each child has its own lifecycle, history, and SLA; parent progress is derived from children.
- Use exactly three core agents: Complaint Analyst, Resolution & Routing, and Monitoring & Escalation. They return bounded, structured recommendations. They cannot directly authorize or commit application actions.
- Persist SLA deadlines and process them with a deterministic, recoverable scheduled worker. Invoke Monitoring & Escalation only after a valid event requires reasoning; do not use an LLM for deadline polling.
- Officer resolution is a submission for verification, not closure. The citizen is notified and receives a proof card with confirm/dispute actions during the 48-hour decision window. If there is no response at 48 hours, send a reminder and keep the ticket pending; silence is never confirmation. Disputes go to an assigned Independent Reviewer queue. The intended Samadhan AI policy is that if no response arrives by seven calendar days from verification start, mark the case `VERIFICATION_OVERDUE` and route it to the Independent Reviewer for a reasoned outcome. Calculate the seven-day deadline at the same local wall-clock time seven dates later in the configured jurisdiction timezone, retain timezone context and store the resulting instant in UTC; due means `now >= deadline`. Handle daylight-saving ambiguity by an explicit deterministic jurisdiction rule. Late responses before reviewer assignment follow ordinary verification after state/authorization checks. Once review is queued or assigned, responses remain visible to the reviewer and cannot auto-close or cancel active review; a late dispute does not automatically change priority. Serialize responses, assignment and decisions and record reasoned reviewer outcomes. Silence alone never establishes resolution. This is project policy, not a universal municipal rule. Parent closure normally requires completed child workflows; exceptional parent closure is a separately granted Senior Authority action with reason and audit.
- Persist in-app notification intent and outcomes. Email and other external channels are optional adapters; delivery failure must not undo complaint state.
- Start with a modular monolith and PostgreSQL. Add workers and durable job/event handling where asynchronous AI, notification, and deadline recovery require them. Do not add services or infrastructure without a concrete need.

## Target technology direction

The supplied blueprint recommends Python/FastAPI, Pydantic, SQLAlchemy, Alembic, PostgreSQL, pgvector for policy retrieval, LangGraph for the three-agent workflow, provider-independent model adapters, a scheduled Python worker, private object storage, JWT-based staff security, React with JavaScript, and FastAPI OpenAPI. These are target recommendations, not all approved or integrated. Model/provider, hosting, object storage, scheduler/job-claim strategy, concrete versions, and external channels require review and a practical prototype. A free demonstration host must not be described as providing continuous monitoring unless its operating guarantees support that claim.

## Explicit scope boundaries

- Duplicate detection/consolidation, heatmaps, predictive maintenance, dynamic SLA/resource allocation, multilingual/voice reporting, IoT, and live municipal integrations are future scope unless separately approved. Duplicate reports must not be merged or rejected autonomously.
- No general-purpose agent tool access or additional core agents. MCP is only for a concrete integration need.
- Sample policies must be labelled as demonstration data, never represented as official municipal rules.
- Image upload requires decoded-content validation, configured type/size/dimension limits, safe normalization/metadata handling, private storage, and access-controlled retrieval before it is enabled for real users.

## Decisions still requiring owners/approval

1. Anonymous intake/tracking design: generate a secure high-entropy token, return it only in a protected response, persist only a server-key HMAC verifier and key identifier/version, and load keys from deployment secret management. Never log the token/key or treat complaint ID as a credential. Revoke by invalidating/replacing the verifier; do not promise account-style recovery for a lost token without independent identity proof. Exact encoding, expiry/renewal defaults, key rotation procedure, rate-limit thresholds and recovery channel require security/implementation review.
2. Staff identity provider, role/capability matrix, department/jurisdiction scopes, and independent reviewer separation of duties.
3. Official taxonomy, ward boundaries, department responsibility data, SLA values/calendars, escalation hierarchy, and evidence requirements. Demo values must be labelled. Initial category candidates are roads/potholes, garbage/sanitation, drainage/sewage, water/leakage, streetlights/electrical infrastructure, damaged public infrastructure, and other/uncertain.
4. Reminder delivery; reviewer mapping/outcomes and authority; the jurisdiction's deterministic daylight-saving ambiguity rule; and exceptional parent closure authority. Late-response handling is documented as the default: process before reviewer assignment, preserve for reviewer during active review, no automatic closure/cancellation, and no automatic reprioritization for a late dispute. The seven-calendar-day overdue-review threshold and its calendar-time semantics are intended project policy.
5. Image/object storage, original-versus-normalized evidence handling, malware/content scanning, retention/deletion, model-provider data handling, and permitted image-analysis scope.
6. Hosting/runtime limits, durable scheduler/job claiming, provider/model selection, email channel, deployment, backup/recovery, and measurable release targets.

## Implementation status

The current backend implements authenticated image-first complaint intake, normalized private local media storage, durable asynchronous Complaint Analyst jobs, analysis result/status persistence, owner-scoped complaint tracking, and a capability-protected read-only analysis review queue with image access. Location is currently optional text only. Approved deterministic priority/safety policy, production object storage/scanning, review assignment/dispositions/retries, broader staff workflows, parent/child tickets, routing, SLA workers, notifications, and citizen verification remain unimplemented. See [backend status](../../backend/README.md). Requirements and architecture documents should be read as target/planning documents unless they explicitly identify an implemented and verified slice.
