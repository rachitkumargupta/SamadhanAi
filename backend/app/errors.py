import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


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
        )

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, dict) else {}
        error = {
            "code": str(detail.get("code", "request_rejected")),
            "message": str(detail.get("message", "The request could not be completed.")),
            "correlation_id": correlation_id(request),
        }
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": error},
            headers=exc.headers,
        )

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        request_id = correlation_id(request)
        logger.exception("Unhandled request failure; correlation_id=%s", request_id)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "The request could not be completed.",
                    "correlation_id": request_id,
                }
            },
        )
