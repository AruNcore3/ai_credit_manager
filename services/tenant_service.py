from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib

from sqlalchemy.orm import Session

from models.account import Account
from models.users import User
from models.wallet import add_credits
from models.api_key import ApiKey
from utils.api_keys import generate_api_key, get_key_prefix, hash_api_key


class QuotaExceededError(ValueError):
    pass


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def signup_tenant_user(
    db: Session,
    *,
    account_name: str,
    username: str,
    email: str,
    password: str,
) -> tuple[Account, User, ApiKey, str]:
    if db.query(Account).filter(Account.name == account_name).one_or_none() is not None:
        raise ValueError("account name already exists")
    if db.query(User).filter(User.username == username).one_or_none() is not None:
        raise ValueError("username already exists")
    if db.query(User).filter(User.email == email).one_or_none() is not None:
        raise ValueError("email already exists")

    account = Account(name=account_name.strip())
    db.add(account)
    db.flush()

    user = User(
        account_id=account.id,
        username=username.strip(),
        email=email.strip().lower(),
        password_hash=_hash_password(password),
        is_active=True,
    )
    db.add(user)
    db.flush()

    raw_key = generate_api_key()
    key_row = ApiKey(
        user_id=user.id,
        name="default",
        key_prefix=get_key_prefix(raw_key),
        key_hash=hash_api_key(raw_key),
    )
    db.add(key_row)
    db.commit()
    db.refresh(account)
    db.refresh(user)
    db.refresh(key_row)
    return account, user, key_row, raw_key


def enforce_account_usage_quota(db: Session, account: Account, spend_credits: int) -> None:
    now = datetime.now(timezone.utc)
    period_start = account.period_started_at

    if period_start.tzinfo is None:
        period_start = period_start.replace(tzinfo=timezone.utc)

    if now >= period_start + timedelta(days=30):
        account.period_started_at = now
        account.period_spend_credits = 0

    projected = account.period_spend_credits + spend_credits
    if projected > account.monthly_credit_quota:
        raise QuotaExceededError("monthly quota exceeded for this account")

    account.period_spend_credits = projected


def admin_credit_adjustment(db: Session, *, user_id: int, amount: int, reason: str) -> None:
    add_credits(db, user_id=user_id, amount=amount, entry_type="admin_adjustment", reference=f"admin:{reason}")
    db.commit()
