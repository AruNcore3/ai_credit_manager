from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from models.audit_event import AuditEvent


def log_audit_event(
    db: Session,
    *,
    actor_type: str,
    actor_id: str,
    action: str,
    target_type: str,
    target_id: str,
    account_id: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    event = AuditEvent(
        actor_type=actor_type,
        actor_id=actor_id,
        account_id=account_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        metadata_json=json.dumps(metadata) if metadata else None,
    )
    db.add(event)
