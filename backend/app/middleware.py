"""Small ASGI middleware for request limits that must run before form parsing."""

from __future__ import annotations

from uuid import uuid4

from starlette.responses import JSONResponse


class RequestBodyLimitMiddleware:
    def __init__(self, app, *, path: str, method: str, maximum_bytes: int):
        self.app = app
        self.path = path
        self.method = method
        self.maximum_bytes = maximum_bytes

    async def __call__(self, scope, receive, send):
        if (
            scope["type"] != "http"
            or scope.get("path") != self.path
            or scope.get("method") != self.method
        ):
            await self.app(scope, receive, send)
            return

        content_length = next(
            (value for name, value in scope.get("headers", []) if name.lower() == b"content-length"),
            None,
        )
        if content_length is not None:
            try:
                if int(content_length) > self.maximum_bytes:
                    await self._reject(scope, receive, send)
                    return
            except ValueError:
                await self._reject(scope, receive, send)
                return

        received = 0

        async def limited_receive():
            nonlocal received
            message = await receive()
            if message.get("type") == "http.request":
                received += len(message.get("body", b""))
                if received > self.maximum_bytes:
                    raise _BodyTooLarge
            return message

        try:
            await self.app(scope, limited_receive, send)
        except _BodyTooLarge:
            await self._reject(scope, receive, send)

    async def _reject(self, scope, receive, send):
        state = scope.setdefault("state", {})
        correlation_id = state.get("correlation_id") or str(uuid4())
        state["correlation_id"] = correlation_id
        response = JSONResponse(
            status_code=413,
            content={
                "error": {
                    "code": "request_too_large",
                    "message": "Complaint upload exceeds the request limit.",
                    "correlation_id": correlation_id,
                }
            },
            headers={"X-Correlation-ID": correlation_id},
        )
        await response(scope, receive, send)


class _BodyTooLarge(Exception):
    pass
