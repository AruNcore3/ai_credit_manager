"""Create or fetch Stripe Customer ids and persist them on ``User``."""

from __future__ import annotations

import os

import stripe
from sqlalchemy.orm import Session

from models.users import User


def _ensure_stripe_api_key() -> None:
    key = os.environ.get("STRIPE_SECRET_KEY")
    if not key:
        raise RuntimeError("STRIPE_SECRET_KEY is not set (check your .env)")
    stripe.api_key = key


def get_or_create_stripe_customer_id(db: Session, user: User) -> str:
    """
    Return ``user.stripe_customer_id`` if already set; otherwise create a
    Stripe Customer, save ``cus_...`` on the user row, and return it.

    Call this before Checkout / SetupIntent / off-session PaymentIntent flows
    so Stripe always has a Customer to attach payment methods to.
    """
    if user.stripe_customer_id:
        return user.stripe_customer_id

    _ensure_stripe_api_key()
    customer = stripe.Customer.create(
        email=user.email,
        name=user.username,
        metadata={"app_user_id": str(user.id)},
    )
    user.stripe_customer_id = customer.id
    db.add(user)
    db.flush()
    return customer.id
