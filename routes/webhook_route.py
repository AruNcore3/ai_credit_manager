import logging

import stripe
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session
from app.config import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET
from app.database import get_db
from app.observability import observability
from services.webhook_processor_service import process_stripe_event
from services.webhook_reliability_service import (
    mark_failed,
    mark_processed,
    upsert_webhook_event,
)

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
        is_alert = observability.increment_event("stripe_webhook_invalid_signature")
        logger.warning("stripe_webhook_invalid_signature")
        if is_alert:
            logger.error("alert_triggered type=webhook_signature_failures threshold_window=60s")
        raise HTTPException(status_code=400, detail="invalid webhook signature")

    event_id = event.get("id", "unknown")
    event_type = event.get("type", "unknown")
    upsert_webhook_event(
        db,
        provider="stripe",
        event_id=event_id,
        event_type=event_type,
        payload=event,
    )
    db.commit()
    try:
        process_stripe_event(db, event)
        mark_processed(db, event_id)
        db.commit()
    except Exception as exc:
        db.rollback()
        row = mark_failed(db, event_id=event_id, error_message=str(exc))
        db.commit()
        is_alert = observability.increment_event("webhook_processing_error")
        logger.exception(
            "webhook_processing_error event_id=%s event_type=%s attempts=%s error=%s",
            event_id,
            event_type,
            row.attempts if row else None,
            str(exc),
        )
        if is_alert:
            logger.error("alert_triggered type=webhook_processing_errors threshold_window=60s")
        raise HTTPException(status_code=500, detail="webhook processing failed")

    return {"received": True}
