from __future__ import annotations

from datetime import datetime
from sqlalchemy.orm import Session

from models.api_key import ApiKey
from utils.api_keys import generate_api_key, get_key_prefix, hash_api_key


def create_api_key(db: Session, *, user_id: int, name: str) -> tuple[ApiKey, str]:
    if not name or not name.strip():
        raise ValueError("name is required")

    raw_key = generate_api_key()
    row = ApiKey(
        user_id=user_id,
        name=name.strip(),
        key_prefix=get_key_prefix(raw_key),
        key_hash=hash_api_key(raw_key),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row, raw_key


def list_api_keys(db: Session, *, user_id: int) -> list[ApiKey]:
    return (
        db.query(ApiKey)
        .filter(ApiKey.user_id == user_id)
        .order_by(ApiKey.created_at.desc())
        .all()
    )


def revoke_api_key(db: Session, *, user_id: int, key_id: int) -> ApiKey:
    row = (
        db.query(ApiKey)
        .filter(ApiKey.id == key_id, ApiKey.user_id == user_id)
        .one_or_none()
    )
    if row is None:
        raise ValueError("api key not found")
    if row.revoked_at is None:
        row.revoked_at = datetime.now()
        db.commit()
        db.refresh(row)
    return row


def rotate_api_key(
    db: Session, *, user_id: int, key_id: int, name: str | None = None
) -> tuple[ApiKey, str]:
    old_key = revoke_api_key(db, user_id=user_id, key_id=key_id)
    new_name = name.strip() if name and name.strip() else old_key.name
    return create_api_key(db, user_id=user_id, name=new_name)
