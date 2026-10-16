# API guidelines and proposed endpoint inventory

**Status:** Planning contract; no endpoints are implemented.<br>
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

The authentication scheme is TBD. Every protected endpoint must receive an authenticated actor context and enforce capability plus resource scope server-side. Citizen access must be scoped to the citizen’s permitted complaint(s); staff access must be bounded by approved assignment, department, and jurisdiction permissions. Admin endpoints require explicit capabilities and audit records. Authentication failures and authorization denials use the stable error contract in [error handling](error-handling.md).

Anonymous intake and reference-code-only tracking require a separate policy decision, abuse controls, and access recovery design; they are not implied by these routes.

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

- JSON is the default content type unless an approved upload flow requires a different content type.
- Use separate create/update/response schemas. Do not bind persistence entities directly to public responses.
- Normalize field validation errors with stable field paths and codes.
- For state transitions, use explicit action endpoints or a transition resource only after the lifecycle state machine is approved. Do not allow arbitrary client-supplied status strings.
- For dates, require explicit timezone offsets for client-supplied instants; server-calculated SLA deadlines remain authoritative.
- Document nullability, optional fields, maximum lengths, and privacy classification in the schema.

## 7. Candidate endpoint inventory

Paths below are proposals and may change when authentication, lifecycle, and API version policies are approved.

| Method and path | Purpose | Candidate access | Request/response considerations |
|---|---|---|---|
| `POST /api/v1/complaints` | Submit a complaint | Citizen; anonymous policy TBD | Validate approved fields; optional idempotency key; return public reference, initial state, and permitted acknowledgement. |
| `GET /api/v1/complaints` | List/search complaints | Citizen own records or scoped staff | Enforce actor scope before filtering; bounded pagination; allowlisted filters/sort; role-specific projection. |
| `GET /api/v1/complaints/{reference}` | Retrieve complaint | Owner or authorized staff | Non-disclosing not-found/forbidden policy; only permitted fields. |
| `GET /api/v1/complaints/{reference}/events` | Retrieve visible history | Owner or authorized staff | Citizen-safe event projection; pagination and stable ordering. |
| `POST /api/v1/complaints/{reference}/information` | Provide requested information | Owner or authorized staff | Validate active request/context; idempotency and attachment rules; record response event. |
| `POST /api/v1/complaints/{reference}/information-requests` | Request additional information | Authorized officer/supervisor | Reason/request schema, actor scope, citizen-visible wording, SLA/pause policy reference. |
| `POST /api/v1/complaints/{reference}/assignments` | Assign/reassign complaint | Authorized staff/supervisor | Destination must be approved/effective; reason required if policy says; concurrency precondition; audit. |
| `POST /api/v1/complaints/{reference}/progress-events` | Record progress | Assigned/scoped staff | Separate public update from internal note; validate event type; audit and concurrency control. |
| `POST /api/v1/complaints/{reference}/resolution-submissions` | Submit proposed resolution | Assigned/authorized staff | Evidence references and summary; response state remains pending verification. |
| `POST /api/v1/complaints/{reference}/verification-decisions` | Verify or reject resolution | Authorized verifier/supervisor; policy TBD | Decision, reason, policy check, separation of duties, audit; closure only on accepted decision. |
| `POST /api/v1/complaints/{reference}/transitions` | Request an allowed state transition | Actor permitted for that transition | Candidate only; schema is action-specific; arbitrary target state is forbidden. Could be represented by specialized endpoints instead. |
| `GET /api/v1/departments` | Read approved department data | Authenticated users; public fields TBD | Only active/effective records and safe fields. |
| `GET /api/v1/jurisdictions` | Read permitted jurisdiction data | Authenticated users; public fields TBD | Geometry/detail disclosure and search behavior TBD. |
| `GET /api/v1/officers` | Search eligible staff | Scoped staff/admin only | Minimize personal data; filter to authorized department/jurisdiction. |
| `GET /api/v1/admin/sla-rules` | Inspect approved SLA rules | Policy administrator/read capability | Version/effective-date visibility; no secret policy fields. |
| `POST /api/v1/admin/sla-rules` | Create/version an SLA rule | Policy administrator/write capability | Provenance, approval, effective date, overlap checks, and audit. Avoid silent retroactive changes. |
| `GET /api/v1/admin/escalations` | Review escalation queue | Scoped supervisor/admin | Bounded filters and minimum necessary complaint details. |
| `POST /api/v1/admin/escalations/{id}/actions` | Record/execute approved escalation action | Authorized supervisor/admin or explicit system workflow | Allowlisted action, policy reference, idempotency, authorization, and outcome record. |
| `GET /api/v1/notifications` | Inspect notification outcomes | Recipient or authorized staff | Scope recipient/complaint details; distinguish pending, delivered, failed, and unknown. |
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
- Attachment upload/download flow, limits, scanning, storage and content authorization.
- Notification preferences and public-safe error/message language.
- OpenAPI ownership, contract test tooling, and API release/deprecation process.
