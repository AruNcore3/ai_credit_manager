from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from models.webhook_delivery import WebhookDelivery


def _max_attempts() -> int:
    return int(os.getenv("WEBHOOK_MAX_ATTEMPTS", "5"))


def _base_retry_seconds() -> int:
    return int(os.getenv("WEBHOOK_RETRY_BASE_SECONDS", "60"))


def _compute_next_retry(attempts: int) -> datetime:
    # Exponential backoff capped at 1 hour.
    delay = min(_base_retry_seconds() * (2 ** max(attempts - 1, 0)), 3600)
    return datetime.now() + timedelta(seconds=delay)


def upsert_webhook_event(
    db: Session,
    *,
    provider: str,
    event_id: str,
    event_type: str,
    payload: dict[str, Any],
) -> WebhookDelivery:
    row = db.query(WebhookDelivery).filter(WebhookDelivery.event_id == event_id).one_or_none()
    if row is None:
        row = WebhookDelivery(
            provider=provider,
            event_id=event_id,
            event_type=event_type,
            payload_json=json.dumps(payload),
            status="pending",
            attempts=0,
            max_attempts=_max_attempts(),
        )
        db.add(row)
    else:
        row.payload_json = json.dumps(payload)
        row.event_type = event_type
        row.provider = provider
    return row


def mark_processed(db: Session, event_id: str) -> None:
    row = db.query(WebhookDelivery).filter(WebhookDelivery.event_id == event_id).one_or_none()
    if row is None:
        return
    row.status = "processed"
    row.error_message = None
    row.next_retry_at = None
    row.last_attempt_at = datetime.now()
    db.add(row)


def mark_failed(db: Session, *, event_id: str, error_message: str) -> WebhookDelivery | None:
    row = db.query(WebhookDelivery).filter(WebhookDelivery.event_id == event_id).one_or_none()
    if row is None:
        return None
    row.attempts += 1
    row.last_attempt_at = datetime.now()
    row.error_message = error_message[:2000]
    if row.attempts >= row.max_attempts:
        row.status = "dead_letter"
        row.next_retry_at = None
    else:
        row.status = "failed"
        row.next_retry_at = _compute_next_retry(row.attempts)
    db.add(row)
    return row


def mark_replayed(db: Session, *, event_id: str) -> None:
    row = db.query(WebhookDelivery).filter(WebhookDelivery.event_id == event_id).one_or_none()
    if row is None:
        return
    row.status = "replayed"
    row.replayed_at = datetime.now()
    row.error_message = None
    row.next_retry_at = None
    db.add(row)

