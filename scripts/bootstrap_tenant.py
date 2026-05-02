from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from models.account import Account
from models.api_key import ApiKey
from models.users import User
from utils.api_keys import generate_api_key, get_key_prefix, hash_api_key


def bootstrap_tenant(
    *,
    account_name: str,
    username: str,
    email: str,
    key_name: str,
    password_hash: str = "bootstrap",
) -> str:
    db = SessionLocal()
    try:
        account = db.query(Account).filter(Account.name == account_name).one_or_none()
        if account is None:
            account = Account(name=account_name)
            db.add(account)
            db.flush()

        user = db.query(User).filter(User.email == email).one_or_none()
        if user is None:
            user = User(
                account_id=account.id,
                username=username,
                email=email,
                password_hash=password_hash,
                is_active=True,
            )
            db.add(user)
            db.flush()

        raw_key = generate_api_key()
        api_key_row = ApiKey(
            user_id=user.id,
            name=key_name,
            key_prefix=get_key_prefix(raw_key),
            key_hash=hash_api_key(raw_key),
        )
        db.add(api_key_row)
        db.commit()
        return raw_key
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap first tenant/user/api key.")
    parser.add_argument("--account-name", default="default-account")
    parser.add_argument("--username", default="owner")
    parser.add_argument("--email", default="owner@example.com")
    parser.add_argument("--key-name", default="bootstrap-key")
    parser.add_argument("--password-hash", default="bootstrap")
    args = parser.parse_args()

    raw_key = bootstrap_tenant(
        account_name=args.account_name,
        username=args.username,
        email=args.email,
        key_name=args.key_name,
        password_hash=args.password_hash,
    )
    print(raw_key)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
