from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi import Request

from backend.app.errors import install_error_handlers
from backend.app.routes import router as complaints_router


app = FastAPI(title="Samadhan AI API", version="0.1.0")
app.include_router(complaints_router)
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
