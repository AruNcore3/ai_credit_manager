from pathlib import Path

from dotenv import load_dotenv

# Load project-root `.env` so Stripe keys work in PowerShell / IDE (not only fish + activate.fish).
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from fastapi import FastAPI, Request

from routes.payment_route import router as payment_router
from routes.webhook_route import router as webhook_router
from routes.credit_route import router as credit_router
from routes.usage_route import router as usage_router
from routes.api_key_route import router as api_key_router
app = FastAPI()

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


