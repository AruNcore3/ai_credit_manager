from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from services.credit_service import apply_paid_topup_once

logger = logging.getLogger(__name__)


def process_stripe_event(db: Session, event: dict) -> None:
    event_type = event["type"]
    logger.info("stripe_webhook_received event_type=%s", event_type)

    if event_type == "payment_intent.succeeded":
        pi = event["data"]["object"]
        payment_intent_id = pi["id"]
        try:
            raw_metadata = pi["metadata"]
            metadata = dict(raw_metadata) if raw_metadata else {}
        except Exception:
            metadata = {}
        logger.info("stripe_webhook_metadata metadata=%s", metadata)

        attempt_id = metadata.get("topup_attempt_id")
        if attempt_id is None:
            logger.warning("missing_attempt_id_in_metadata payment_intent_id=%s", payment_intent_id)
            applied = apply_paid_topup_once(db, payment_intent_id=payment_intent_id)
        else:
            try:
                parsed_attempt_id = int(attempt_id)
            except (TypeError, ValueError):
                logger.warning(
                    "invalid_attempt_id_in_metadata topup_attempt_id=%s payment_intent_id=%s",
                    attempt_id,
                    payment_intent_id,
                )
                applied = False
            else:
                applied = apply_paid_topup_once(
                    db,
                    attempt_id=parsed_attempt_id,
                    payment_intent_id=payment_intent_id,
                )
        logger.info(
            "stripe_payment_intent_succeeded payment_intent_id=%s credits_applied=%s",
            payment_intent_id,
            applied,
        )
    else:
        logger.info("stripe_webhook_ignored event_type=%s", event_type)

