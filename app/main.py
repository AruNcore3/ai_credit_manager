from pathlib import Path
import os
import logging

from dotenv import load_dotenv

# Load project-root `.env` so Stripe keys work in PowerShell / IDE (not only fish + activate.fish).
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Ensure all SQLAlchemy models are imported so relationship() string targets resolve.
import models  # noqa: F401

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from routes.payment_route import router as payment_router
from routes.webhook_route import router as webhook_router
from routes.credit_route import router as credit_router
from routes.usage_route import router as usage_router
from routes.api_key_route import router as api_key_router
from app.rate_limit import build_rate_limiter

logger = logging.getLogger(__name__)
app = FastAPI()
rate_limiter = build_rate_limiter()

@app.get("/")
def home():
    return {"message": "Hello, World!"}

@app.middleware("http")
async def legacy_deprecation_middleware(request: Request, call_next):
    response = await call_next(request)

    legacy_prefixes = ("/payments", "/credits", "/webhooks")
    if request.url.path.startswith(legacy_prefixes):
        response.headers["Deprecation"] = "true"
        response.headers["Sunset"] = "Tue, 24 Jun 2026 00:00:00 GMT"

    return response


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if not request.url.path.startswith("/v1"):
        return await call_next(request)

    key = request.headers.get("X-API-Key") or (request.client.host if request.client else "anonymous")
    include_path = os.getenv("RATE_LIMIT_INCLUDE_PATH", "false").strip().lower() in {"1", "true", "yes", "on"}
    scope = request.url.path if include_path else None
    decision = rate_limiter.check(key, scope=scope)

    if not decision.allowed:
        logger.warning(
            "rate_limit_exceeded path=%s scope=%s key=%s limit=%s reset_after=%s",
            request.url.path,
            scope,
            key[:16],
            decision.limit,
            decision.reset_after,
        )
        return JSONResponse(
            status_code=429,
            content={"detail": "rate limit exceeded"},
            headers={
                "Retry-After": str(decision.reset_after),
                "X-RateLimit-Limit": str(decision.limit),
                "X-RateLimit-Remaining": "0",
            },
        )

    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(decision.limit)
    response.headers["X-RateLimit-Remaining"] = str(decision.remaining)
    return response

# Versioned routes
app.include_router(payment_router, prefix="/v1")
app.include_router(webhook_router, prefix="/v1")
app.include_router(credit_router, prefix="/v1")
app.include_router(usage_router)
app.include_router(api_key_router,prefix="/v1")

# Temporary legacy routes (deprecated by middleware header)
app.include_router(payment_router)
app.include_router(webhook_router)
app.include_router(credit_router)
