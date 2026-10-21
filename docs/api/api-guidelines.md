# API guidelines and proposed endpoint inventory

**Status:** Target API contract. Current citizen intake/tracking and liveness endpoints are implemented partially; target image, staff, worker, verification, and notification endpoints are not yet implemented.<br>
**Related:** [Functional requirements](../requirements/functional-requirements.md), [roles and use cases](../requirements/user-roles-and-use-cases.md), [error handling](error-handling.md)

## 1. Contract principles

- HTTP is a boundary adapter to application use cases; route handlers must not own business policy or call the database/LLM directly.
- Validate request shape and semantic constraints before use-case execution. Validate authorization and object scope in application logic for every operation.
- Publish request/response schemas and the OpenAPI contract. Treat citizen-facing and staff-facing representations as distinct projections.
- Use stable public complaint references; do not expose sequential internal database IDs by default.
- Return only fields required by the requesting role. Never reveal staff-only notes, internal prompt/context, secrets, stack traces, or another citizen’s existence.
- Use explicit pagination, filtering, sorting, concurrency, and idempotency behavior. Bound body size, page size, and provider-triggering operations.
- Serialize timestamps in an agreed timezone-aware format (UTC recommended for instants); keep local jurisdiction calendars in policy data rather than client assumptions.

## 2. Versioning and naming proposal

Use a versioned prefix such as `/api/v1` for the initial public contract. Resource names are plural, lowercase, and stable (for example, `/complaints`). Use HTTP methods according to resource intent and document every state-changing operation. Avoid exposing database table names or agent-specific implementation details.

Breaking changes require a version/deprecation decision. The team must choose compatibility window, sunset process, and whether staff/internal APIs share the same version boundary before launch.

## 3. Authentication and authorization

The current citizen slice verifies externally issued HS256 JWTs. The target requires JWT-based protected staff operations and role/department/jurisdiction scope. Anonymous complaint submission and tracking are supported project policy; tracking must use a high-entropy secret whose verifier/hash is stored server-side, never the public complaint ID alone. Apply rate limits and non-enumerating access responses. Every endpoint enforces capability and resource scope server-side. Citizen verification, Independent Reviewer decisions, Department Administrator actions, and exceptional Senior Authority closure are distinct capabilities enforced by backend state-transition logic and audit. The original officer cannot be the sole reviewer of their own resolution.

Reference-code-only tracking is not supported. The target anonymous flow uses a separate high-entropy secret and server-key verifier, with abuse controls and revocation. Lost-token account-style recovery is not promised without independent identity proof. Implement the credential controls before enabling the flow.

## 4. Collections, pagination, and concurrency

- Collection endpoints must use a documented cursor or offset pagination scheme, enforce a maximum page size, and return a continuation indicator.
- Sort fields and filter keys must be allowlisted; default ordering must be stable.
- Response totals should be omitted unless needed and safe to calculate.
- State-changing requests should include a concurrency precondition (for example, an entity version or ETag/`If-Match`) where stale updates could overwrite newer decisions.
- A stale precondition returns a conflict/precondition error and does not silently overwrite current state.

The first backend slice provisionally uses `limit`/`offset`, with bounded page sizes and a `next_offset` response field. Confirm or replace this before frontend integration; cursor pagination may be preferable if collection size or concurrent insert behavior requires it. Concurrency precondition format remains undecided.

## 5. Idempotency and retries

For writes that could be retried after a network timeout, define an idempotency key scope, retention period, actor binding, and payload mismatch behavior. At minimum consider complaint submission and provider side effects. Reusing a key with the same request should return the original outcome; using it with a materially different request should be rejected. Idempotency records must not expose another actor’s data.

Clients should retry only documented retryable errors and should use bounded backoff. The server must never report provider delivery as successful when the outcome is unknown.

## 6. Request and response conventions

- Image-first complaint intake requires an upload contract (multipart or pre-authorized private-storage upload) with decoded-content validation; do not expose raw/public object-storage URLs. Exact upload flow is pending design.
- JSON is the default content type for non-media operations.
- Use separate create/update/response schemas. Do not bind persistence entities directly to public responses.
- Normalize field validation errors with stable field paths and codes.
- For state transitions, use explicit action endpoints or a transition resource only after the lifecycle state machine is approved. Do not allow arbitrary client-supplied status strings.
- For dates, require explicit timezone offsets for client-supplied instants; server-calculated SLA deadlines remain authoritative.
- Document nullability, optional fields, maximum lengths, and privacy classification in the schema.

## 7. Candidate endpoint inventory

Paths below are proposals and may change when authentication, lifecycle, and API version policies are approved.

| Method and path | Purpose | Candidate access | Request/response considerations |
|---|---|---|---|
| `POST /api/v1/complaints` | Submit image-first complaint | Citizen or anonymous complainant using secret-based tracking | Required image, optional text, GPS/manual location; validate and persist complaint/media reference/event/durable analysis-job intent before AI; return reference and initial processing status, and securely deliver the anonymous tracking secret once. |
| `GET /api/v1/complaints` | List/search complaints | Citizen own records or scoped staff | Enforce actor scope before filtering; bounded pagination; allowlisted filters/sort; role-specific projection. |
| `GET /api/v1/complaints/{reference}` | Retrieve complaint | Owner or authorized staff | Non-disclosing not-found/forbidden policy; public status, permitted assigned department/progress, parent/child rollup, and resolution proof-card/evidence projection only where authorized. |
| `GET /api/v1/complaints/{reference}/timeline` (current slice: `/events`) | Retrieve visible history | Owner or authorized staff | Citizen-safe event projection; pagination/stable ordering; include permitted parent/child progress and resolution evidence references. |
| `POST /api/v1/complaints/{reference}/additional-information` | Provide requested details | Owner or authorized staff | Validate active request; persist response/event; resume analysis workflow safely. |
| `POST /api/v1/complaints/{reference}/information` | Provide requested information | Owner or authorized staff | Validate active request/context; idempotency and attachment rules; record response event. |
| `POST /api/v1/complaints/{reference}/information-requests` | Request additional information | Authorized officer/supervisor | Reason/request schema, actor scope, citizen-visible wording, SLA/pause policy reference. |
| `POST /api/v1/complaints/{reference}/assignments` | Assign/reassign complaint | Authorized staff/supervisor | Destination must be approved/effective; reason required if policy says; concurrency precondition; audit. |
| `GET /api/v1/officer/complaints` | List authorized work tickets | Scoped officer | Filter to current assignment/department/jurisdiction; bounded results. |
| `GET /api/v1/officer/workload` | View officer's own workload indicators | Scoped officer | Return only own authorized workload and SLA indicators. |
| `POST /api/v1/complaints/{reference}/accept` | Accept assignment | Assigned officer | Verify assignment/scope and current ticket state; record event. |
| `POST /api/v1/complaints/{reference}/reject` | Reject assignment with reason | Assigned officer | Require reason; record rejection and route repeated conflict to review; do not allow uncontrolled department bouncing. |
| `POST /api/v1/complaints/{reference}/progress` | Record progress | Assigned/scoped staff | Separate public update from internal note; validate event type; audit and concurrency control. |
| `POST /api/v1/complaints/{reference}/resolution` | Submit proposed resolution | Assigned/authorized staff | Evidence references and summary; response state remains pending verification. |
| `POST /api/v1/complaints/{reference}/verification` | Confirm or dispute own complaint's resolution | Citizen with authorized complaint access | Citizen action only on own complaint; confirmation initiates authorized normal closure, dispute creates an assigned review case; at 48 hours without response send reminder and keep pending; silence is never confirmation. Before reviewer assignment, process a late response under ordinary verification rules; during active review preserve it for the reviewer and do not auto-close/cancel review. |
| `GET /api/v1/reviewer/cases` | Inspect assigned dispute and overdue-verification cases | Assigned Independent Reviewer | Scope to assigned cases; overdue-verification cases follow the intended seven-calendar-day policy; reviewer cannot be the original officer acting as sole reviewer. |
| `POST /api/v1/reviewer/cases/{case_id}/decision` | Record reasoned independent-review outcome | Assigned Independent Reviewer | Record outcome, rationale, evidence references and audit event; close or return/reopen only through explicitly granted transitions. A missing citizen response alone cannot justify closure. |
| `POST /api/v1/complaints/{parent_reference}/exceptional-closure` | Exceptional parent closure | Explicitly authorized Senior Authority | Require reason, current-version precondition, and audit event; do not change or conceal unresolved child states. This grant does not imply Independent Reviewer permission. |
| `POST /api/v1/admin/routing-review` | Record authorized resolution of a routing conflict | Scoped routing reviewer/admin | Validate references, reason, scope, current ticket version and audit disposition. This does not grant Independent Reviewer authority for resolution disputes. |
| `POST /api/v1/complaints/{reference}/transitions` | Request an allowed state transition | Actor permitted for that transition | Candidate only; schema is action-specific; arbitrary target state is forbidden. Could be represented by specialized endpoints instead. |
| `GET /api/v1/departments` | Read approved department data | Authenticated users; public fields TBD | Only active/effective records and safe fields. |
| `GET /api/v1/jurisdictions` | Read permitted jurisdiction data | Authenticated users; public fields TBD | Geometry/detail disclosure and search behavior TBD. |
| `POST /api/v1/admin/departments` / `officers` / `jurisdictions` | Maintain approved reference data | Explicitly scoped administrator | Validate source/provenance/effective status and audit changes. |
| `POST /api/v1/admin/sla-policies` | Create/version an SLA policy | Policy administrator/write capability | Provenance, approval, effective date, overlap checks, and audit. Avoid silent retroactive changes. |
| `GET /api/v1/admin/escalations` | Review escalation queue | Scoped supervisor/admin | Bounded filters and minimum necessary details; breach events originate from deterministic worker. |
| `POST /api/v1/admin/escalations/{id}/actions` | Record/execute approved escalation action | Authorized supervisor/admin or explicit system workflow | Allowlisted action, policy reference, idempotency, authorization, and outcome record. |
| `GET /api/v1/admin/audit-logs` | Inspect permitted audit records | Separately authorized auditor/admin | Strict scope, pagination, privacy filtering and access audit. |
| `GET /api/v1/admin/analytics` | View ward/department performance summaries | Scoped administrator | Aggregated metrics only; enforce department/jurisdiction scope and avoid unnecessary complaint details. |
| `GET /api/v1/notifications` | Inspect in-app notification outcomes | Recipient or authorized staff | Scope recipient/complaint details; distinguish pending, delivered, failed, and unknown. Email is optional. |
| Internal worker interfaces | Claim jobs, analyze complaints, process due SLAs and verification deadlines, dispatch events/notifications | Service identity only; not public endpoints | Durable idempotent processing, bounded retries, jurisdiction-timezone deadline calculation, current-state/deadline revalidation, downtime recovery. Monitoring & Escalation is invoked from valid events only. Do not treat PostgreSQL storage as a scheduler by itself. |
| `GET /health/live` | Process liveness | Platform/operations | Minimal response; no credentials, versions, or topology. |
| `GET /health/ready` | Readiness for intended service | Platform/operations | Report only necessary readiness; define whether optional AI/provider outages affect readiness. |

No AI-invocation endpoint is proposed for citizen clients. Agent invocation should normally be initiated by application workflows or authorized internal operations, with bounded permissions and audit.

## 8. Error responses

Use the stable error envelope and status mapping in [error handling](error-handling.md). Errors must include a safe human-readable message and correlation ID; detailed validation information must not expose sensitive values. Do not embed provider stack traces, model prompts, SQL errors, or secrets.

## 9. Open API decisions

- Authentication mechanism, token/session lifecycle, citizen access recovery, anonymous access, and resource scopes.
- API versioning and compatibility window; separate public and staff contract requirements.
- Public complaint reference format and anti-enumeration behavior.
- Pagination, filtering, sorting, concurrency precondition, and idempotency formats.
- Exact state/action endpoints after state machine approval.
- Image upload/download flow, limits, normalization/scanning, private storage, retention and content authorization.
- Location payload/source, geospatial boundary representation, and jurisdiction lookup contract.
- Parent/child ticket APIs and citizen-facing aggregate timeline.
- Durable worker/job/event schemas, internal authentication, retries, claims and recovery.
- Secure anonymous credential encoding/key rotation, expiry defaults, revocation, rate-limit thresholds and recovery channel; reviewer authority/mapping/outcomes; jurisdiction daylight-saving ambiguity rule; deadline processing/recovery; and reminder delivery/retries. The 48-hour reminder/no-closure-by-silence behavior and seven-calendar-day overdue-review threshold are intended project policy. Late responses before reviewer assignment follow ordinary verification; while review is active they remain visible to the reviewer and cannot auto-close/cancel review.
- Notification preferences and public-safe error/message language.
- OpenAPI ownership, contract test tooling, and API release/deprecation process.
