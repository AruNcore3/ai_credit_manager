from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from models.account import Account  # noqa: F401
from models.users import User


def get_current_user(
    db: Session = Depends(get_db),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> User:
    if not x_api_key:
        raise HTTPException(status_code=401, detail="missing API key")

    user = db.query(User).filter(User.api_key == x_api_key).one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="invalid API key")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="inactive user")

    return user
