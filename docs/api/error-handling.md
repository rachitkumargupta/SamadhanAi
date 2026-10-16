# API error-handling contract

**Status:** Proposed; must be reconciled with the selected framework and approved API contract. No response behavior is implemented yet.

## 1. Goals

- Give clients stable, actionable error codes and safe messages.
- Keep internal diagnostics, personal data, secrets, prompts, and provider details private.
- Distinguish a rejected request from a retryable dependency failure or a stale state conflict.
- Include a correlation ID that support staff can use to find a redacted server-side record.

## 2. Error response shape (proposal)

```json
{
  "error": {
    "code": "validation_error",
    "message": "Review the highlighted fields and try again.",
    "details": [
      {
        "field": "description",
        "code": "required",
        "message": "Enter a description."
      }
    ],
    "correlation_id": "opaque-request-id"
  }
}
```

`details` is optional and should be included only when it is safe and useful. Do not echo raw submitted secrets, full complaint content, access tokens, internal exception text, SQL, prompts, or model/provider responses. The exact serialization (including whether to adopt RFC 9457 Problem Details) remains a team decision.

## 3. Candidate HTTP status and error-code mapping

| HTTP status | Candidate code | Use when | Client behavior |
|---|---|---|---|
| 400 | `invalid_request` | Request cannot be parsed or violates a general request rule. | Correct request; do not retry unchanged. |
| 401 | `authentication_required` | Valid authentication context is absent or invalid. | Authenticate/refresh according to approved auth flow. |
| 403 | `forbidden` | Actor is authenticated but lacks permission. | Do not retry without an authorized role/scope. |
| 404 | `not_found` | Resource does not exist or policy requires hiding its existence from this actor. | Do not infer whether another actor can access it. |
| 409 | `state_conflict` | Requested lifecycle transition is not allowed from current state. | Refresh and present current state/allowed next step. |
| 409 | `idempotency_conflict` | Key was already used with a materially different request. | Use a new key only for a genuinely new action. |
| 409 or 412 | `version_conflict` | Supplied entity version/ETag is stale. | Reload current data and ask user to reconcile. Exact status depends on chosen precondition contract. |
| 413 | `payload_too_large` | Request or attachment exceeds configured limit. | Reduce size; limits should be discoverable. |
| 415 | `unsupported_media_type` | Content type is not supported. | Use an approved content type. |
| 422 | `validation_error` | Parsed fields fail semantic/schema validation. | Correct the specified safe fields. Framework-specific mapping must be consistent. |
| 429 | `rate_limited` | Actor/client exceeds an approved request or provider quota. | Respect `Retry-After` when present and use bounded backoff. |
| 500 | `internal_error` | Unexpected server failure. | Retry only if operation is documented as safe/idempotent; provide correlation ID to support. |
| 502/503/504 | `dependency_unavailable` / `dependency_timeout` | Approved provider is unavailable, rejected a dependency request, or exceeded timeout. | Follow retry guidance; do not assume side effect succeeded. Core complaint state should remain consistent. |

This mapping is provisional. Avoid leaking whether a complaint exists where doing so creates an enumeration or privacy risk. If hiding existence, consistently return the approved response for both absent and inaccessible references.

## 4. Validation details

- Field paths use one consistent notation and identify the input location without echoing the value.
- Multiple safe field errors may be returned together; cap count and message size.
- Separate syntax errors, semantic/business-rule violations, and state conflicts.
- Do not expose internal enum values or staff-only policy language if a plain-language message is required.
- Never claim a write or external delivery succeeded unless the authoritative outcome is known.

## 5. Retry and partial-failure behavior

- Document retryability per operation. Clients must not blindly retry non-idempotent writes.
- For idempotent operations, return a consistent result for a repeated key/request within its retention window.
- If provider outcome is unknown after timeout, report a pending/unknown outcome or return a retry-safe response, then reconcile through the recorded operation; do not report false success or failure.
- Use bounded backoff and honor `Retry-After` where provided. Do not expose provider quota internals.
- A provider failure must not roll back a committed complaint transition unless the product contract makes that provider operation part of the atomic use case (generally avoid this for external calls).

## 6. Logging and correlation

Every response should have a correlation ID (or equivalent response header and body field) that maps to server-side structured logs. Logs should capture error category, route/use case, actor class, dependency, and timing as appropriate, while excluding credentials and unnecessary PII. Restrict access and retention for logs. Client-facing correlation IDs must not encode user IDs, database keys, or secrets.

## 7. Framework and contract decisions

Before implementation, choose:

- RFC 9457 Problem Details or a project-specific envelope;
- exact status/code registry and validation field notation;
- missing-versus-forbidden disclosure behavior;
- correlation ID header/name and propagation across provider calls;
- idempotency replay/conflict response and `Retry-After` conventions;
- mapping of framework validation and unhandled exceptions;
- localization requirements for user-facing messages.

Document these decisions in OpenAPI and add contract tests so all endpoints use the same shape.
