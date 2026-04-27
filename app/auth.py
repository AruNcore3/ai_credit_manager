from datetime import datetime

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from models.api_key import ApiKey
from models.users import User
from utils.api_keys import hash_api_key


def get_current_user(
    db: Session = Depends(get_db),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> User:
    if not x_api_key:
        raise HTTPException(status_code=401, detail="missing API key")

    hashed_key = hash_api_key(x_api_key)
    api_key_row = (
        db.query(ApiKey)
        .filter(ApiKey.key_hash == hashed_key, ApiKey.revoked_at.is_(None))
        .one_or_none()
    )
    if api_key_row is None:
        raise HTTPException(status_code=401, detail="invalid API key")

    user = db.query(User).filter(User.id == api_key_row.user_id).one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="invalid API key")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="inactive user")

    api_key_row.last_used_at = datetime.now()
    db.commit()

    return user
