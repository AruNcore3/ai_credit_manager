import stripe
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session
from app.config import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET
from app.database import get_db
from services.credit_service import apply_paid_topup_once

stripe.api_key = STRIPE_SECRET_KEY
router = APIRouter(prefix="/webhooks", tags=["webhooks"])

@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
):
    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=stripe_signature,
            secret=STRIPE_WEBHOOK_SECRET,
        )
    except Exception:
        raise HTTPException(status_code=400, detail="invalid webhook signature")

    if event["type"] == "payment_intent.succeeded":
        pi = event["data"]["object"]
        apply_paid_topup_once(db, payment_intent_id=pi["id"])

    return {"received": True}
