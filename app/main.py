from pathlib import Path

from dotenv import load_dotenv

# Load project-root `.env` so Stripe keys work in PowerShell / IDE (not only fish + activate.fish).
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from fastapi import FastAPI
from fastapi import Request

from routes.payment_route import router as payment_router
from routes.webhook_route import router as webhook_router
from routes.credit_route import router as credit_router

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Hello, World!"}



app.include_router(payment_router)
app.include_router(webhook_router)
app.include_router(credit_router)
