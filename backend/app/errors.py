import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


logger = logging.getLogger(__name__)


def correlation_id(request: Request) -> str:
    return getattr(request.state, "correlation_id", "unavailable")


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            {
                "field": ".".join(str(part) for part in error.get("loc", ())[1:]),
                "code": str(error.get("type", "invalid")),
                "message": "Value is invalid or missing.",
            }
            for error in exc.errors()[:50]
        ]
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "Review the submitted fields and try again.",
                    "details": details,
                    "correlation_id": correlation_id(request),
                }
            },
            headers={"X-Correlation-ID": correlation_id(request)},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, dict) else {}
        request_id = correlation_id(request)
        error = {
            "code": str(detail.get("code", "request_rejected")),
            "message": str(detail.get("message", "The request could not be completed.")),
            "correlation_id": request_id,
        }
        headers = dict(exc.headers or {})
        headers["X-Correlation-ID"] = request_id
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": error},
            headers=headers,
        )

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        request_id = correlation_id(request)
        logger.error(
            "Unhandled request failure; correlation_id=%s error_type=%s",
            request_id,
            type(exc).__name__,
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "The request could not be completed.",
                    "correlation_id": request_id,
                }
            },
            headers={"X-Correlation-ID": request_id},
        )
