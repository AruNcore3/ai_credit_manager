from pathlib import Path

from dotenv import load_dotenv

# Load project-root `.env` so Stripe keys work in PowerShell / IDE (not only fish + activate.fish).
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from fastapi import FastAPI
from fastapi import Request

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Hello, World!"}

@app.post('/webhook')
def webhook(request: Request):
    return {"message": "Webhook received"}