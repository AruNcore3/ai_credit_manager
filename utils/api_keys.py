from __future__ import annotations

import hashlib
import hmac
import os 
import secrets

KEY_PREFIX = "ak_live_"

def generate_api_key()-> str:
    return f"{KEY_PREFIX}{secrets.token_urlsafe(32)}"

def get_key_prefix(raw_key:str)->str:
    return raw_key[:16]

def hash_api_key(raw_key:str)->str:
    secret = os.getenv("API_KEY_HASH_SECRET")
    if not secret:
        raise RuntimeError("API_KEY_HASH_SECRET is missing")

    digest = hmac.new(
        key=secret.encode("utf-8"),
        msg=raw_key.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()
    return digest

