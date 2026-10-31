from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi import Request

from backend.app.errors import install_error_handlers
from backend.app.middleware import RequestBodyLimitMiddleware
from backend.app.routes import (
    monitoring_router,
    router as complaints_router,
    resolution_router,
    staff_router,
    verification_review_router,
    notifications_router,
)
from backend.app.agents.complaint_analyst import MAX_IMAGE_BYTES


app = FastAPI(title="Samadhan AI API", version="0.1.0")
app.add_middleware(
    RequestBodyLimitMiddleware,
    path="/api/v1/complaints",
    method="POST",
    maximum_bytes=MAX_IMAGE_BYTES + 256_000,
)
app.add_middleware(
    RequestBodyLimitMiddleware,
    path="/api/v1/staff/complaints/",
    method="POST",
    maximum_bytes=MAX_IMAGE_BYTES + 256_000,
    path_prefix=True,
)
app.include_router(complaints_router)
app.include_router(staff_router)
app.include_router(monitoring_router)
app.include_router(resolution_router)
app.include_router(verification_review_router)
app.include_router(notifications_router)
install_error_handlers(app)


@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    candidate = request.headers.get("X-Correlation-ID")
    try:
        request_id = str(UUID(candidate)) if candidate else str(uuid4())
    except (ValueError, TypeError):
        request_id = str(uuid4())
    request.state.correlation_id = request_id
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = request_id
    return response


@app.get("/health/live", tags=["health"])
def liveness() -> dict[str, str]:
    return {"status": "alive"}
