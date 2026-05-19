from pathlib import Path
import os
import logging

from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

# Load `.env` only for local development.
APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
if APP_ENV in {"development", "dev", "local", "test"}:
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)

# Ensure all SQLAlchemy models are imported so relationship() string targets resolve.
import models  # noqa: F401

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from routes.payment_route import router as payment_router
from routes.webhook_route import router as webhook_router
from routes.credit_route import router as credit_router
from routes.usage_route import router as usage_router
from routes.api_key_route import router as api_key_router
from routes.onboarding_route import router as onboarding_router
from routes.admin_route import router as admin_router
from app.rate_limit import build_rate_limiter
from app.database import SessionLocal
from models.api_key import ApiKey
from models.users import User
from utils.api_keys import hash_api_key

logger = logging.getLogger(__name__)
app = FastAPI(
    title="Billbridge API",
    version="1.0.0",
    description="Hosted multi-tenant API for credits, usage metering, payments, and webhooks.",
    contact={"name": "Support", "email": "support@yourdomain.com"},
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/reference",
)
rate_limiter = build_rate_limiter()
cors_allowed_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOW_ORIGINS", "").split(",")
    if origin.strip()
]
if APP_ENV in {"production", "prod"} and not cors_allowed_origins:
    raise RuntimeError("CORS_ALLOW_ORIGINS is required in production")
if cors_allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
        allow_headers=["Content-Type", "X-API-Key", "Idempotency-Key", "X-Admin-Token"],
    )

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

    api_key = request.headers.get("X-API-Key")
    key = request.client.host if request.client else "anonymous"
    if api_key:
        db = None
        try:
            db = SessionLocal()
            hashed = hash_api_key(api_key)
            user = (
                db.query(User)
                .join(ApiKey, ApiKey.user_id == User.id)
                .filter(ApiKey.key_hash == hashed, ApiKey.revoked_at.is_(None))
                .one_or_none()
            )
            if user is not None:
                key = f"tenant:{user.account_id}:key:{hashed[:16]}"
            else:
                key = f"unknown:{hashed[:16]}"
        except Exception:
            key = "anonymous"
        finally:
            if db is not None:
                db.close()
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
app.include_router(onboarding_router, prefix="/v1")
app.include_router(admin_router, prefix="/v1")

# Temporary legacy routes (deprecated by middleware header)
app.include_router(payment_router)
app.include_router(webhook_router)
app.include_router(credit_router)
