import logging

import stripe
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session
from app.config import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET
from app.database import get_db
from services.credit_service import apply_paid_topup_once

stripe.api_key = STRIPE_SECRET_KEY
router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)

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
        logger.warning("stripe_webhook_invalid_signature")
        raise HTTPException(status_code=400, detail="invalid webhook signature")

    event_type = event.get("type", "unknown")
    logger.info("stripe_webhook_received event_type=%s", event_type)

    if event["type"] == "payment_intent.succeeded":
        pi = event["data"]["object"]
        payment_intent_id = pi.get("id")
        attempt_id = int(pi["metadata"]["topup_attempt_id"])
        applied = apply_paid_topup_once(db, attempt_id = attempt_id)
        logger.info(
            "stripe_payment_intent_succeeded payment_intent_id=%s credits_applied=%s",
            payment_intent_id,
            applied,
        )
    else:
        logger.info("stripe_webhook_ignored event_type=%s", event_type)

    return {"received": True}


