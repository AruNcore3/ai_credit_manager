from pathlib import Path
import os
import logging
import time
import uuid

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

from fastapi import Depends, FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from routes.payment_route import router as payment_router
from routes.webhook_route import router as webhook_router
from routes.credit_route import router as credit_router
from routes.usage_route import router as usage_router
from routes.api_key_route import router as api_key_router
from routes.onboarding_route import router as onboarding_router
from routes.admin_route import router as admin_router
from app.rate_limit import build_rate_limiter
from app.observability import observability
from app.auth import require_admin
from app.database import SessionLocal
from models.api_key import ApiKey
from models.users import User
from utils.api_keys import hash_api_key

logger = logging.getLogger(__name__)
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
developer_index = frontend_dir / "index.html"
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
if frontend_dir.exists():
    app.mount("/developer-assets", StaticFiles(directory=str(frontend_dir)), name="developer-assets")

@app.get("/")
def home():
    return {"message": "Hello, World!"}


@app.get("/developer", include_in_schema=False)
def developer_docs():
    if not developer_index.exists():
        return JSONResponse(status_code=404, content={"detail": "developer docs are not available"})
    return FileResponse(developer_index)


@app.get("/developer/{page}", include_in_schema=False)
def developer_page(page: str):
    allowed_pages = {"quickstart", "auth", "sdk", "flow", "install"}
    if page not in allowed_pages:
        return JSONResponse(status_code=404, content={"detail": "page not found"})
    target = frontend_dir / f"{page}.html"
    if not target.exists():
        return JSONResponse(status_code=404, content={"detail": "page not found"})
    return FileResponse(target)


@app.get("/internal/metrics", response_class=PlainTextResponse, dependencies=[Depends(require_admin)])
def metrics():
    return observability.render_prometheus()

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
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    started = time.perf_counter()
    if not request.url.path.startswith("/v1"):
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        observability.observe_request(
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            latency_ms=(time.perf_counter() - started) * 1000,
        )
        return response

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
        observability.increment_event("rate_limit_exceeded")
        logger.warning(
            "rate_limit_exceeded request_id=%s path=%s scope=%s key=%s limit=%s reset_after=%s",
            request_id,
            request.url.path,
            scope,
            key[:16],
            decision.limit,
            decision.reset_after,
        )
        response = JSONResponse(
            status_code=429,
            content={"detail": "rate limit exceeded"},
            headers={
                "Retry-After": str(decision.reset_after),
                "X-RateLimit-Limit": str(decision.limit),
                "X-RateLimit-Remaining": "0",
            },
        )
        response.headers["X-Request-ID"] = request_id
        observability.observe_request(
            method=request.method,
            path=request.url.path,
            status=429,
            latency_ms=(time.perf_counter() - started) * 1000,
        )
        return response

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-RateLimit-Limit"] = str(decision.limit)
    response.headers["X-RateLimit-Remaining"] = str(decision.remaining)
    observability.observe_request(
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        latency_ms=(time.perf_counter() - started) * 1000,
    )
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
