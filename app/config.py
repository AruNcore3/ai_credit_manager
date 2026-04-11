import os

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

if not STRIPE_SECRET_KEY:
    raise RuntimeError("STRIPE_SECRET_KEY is missing")
if not STRIPE_WEBHOOK_SECRET:
    raise RuntimeError("STRIPE_WEBHOOK_SECRET is missing")

