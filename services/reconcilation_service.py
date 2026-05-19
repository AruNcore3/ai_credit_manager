from __future__ import annotations
import os

from datetime import datetime, timedelta
from typing import Dict

import stripe
from sqlalchemy.orm import Session
from sqlalchemy import select 

from app.config import STRIPE_SECRET_KEY
from app.observability import observability
from models.topup_attempt import TopUpAttempt
from services.credit_service import apply_paid_topup_once

import logging
logger = logging.getLogger(__name__)

stripe.api_key = STRIPE_SECRET_KEY

def reconile_initiated_topups(db:Session,older_than_minutes:int=5,limit:int=100)-> Dict[str,int]:

    cutoff = datetime.now() - timedelta(minutes=older_than_minutes)
    stmt = (
        select(TopUpAttempt)
        .where(
            TopUpAttempt.status == "initiated",
            TopUpAttempt.created_at < cutoff,
            TopUpAttempt.stripe_payment_intent_id.isnot(None)
        )
        .limit(limit)
    )

    attempts = db.execute(stmt).scalars().all()

    summary = {
        "checked":0,
        "applied":0,
        "already_paid":0,
        "failed":0,
        "pending":0,
        "error":0
    }

    for attempt in attempts:
        summary["checked"] += 1
        try:
            pi = stripe.PaymentIntent.retrieve(
                attempt.stripe_payment_intent_id
            )
            status = pi.get("status")

            if status == "succeeded":
                applied = apply_paid_topup_once(
                    db=db,
                    attempt_id=attempt.id,
                    payment_intent_id=pi.get("id"),
                )
                if applied:
                    summary["applied"] += 1
                else:
                    summary["already_paid"] += 1
            elif status in ("canceled","requires_payment_method"):
                attempt.status = "failed"
                db.add(attempt)
                db.commit()
                summary["failed"] += 1

            else:
                summary["pending"] +=1

        except Exception as e:
            db.rollback()
            summary["error"] += 1
            is_alert = observability.increment_event("reconciliation_attempt_error")
            logger.exception(
                "reconciliation_attempt_error attempt_id=%s stripe_payment_intent_id=%s error=%s",
                attempt.id,
                attempt.stripe_payment_intent_id,
                str(e),
            )
            if is_alert:
                logger.error("alert_triggered type=reconciliation_errors threshold_window=60s")
    return summary

