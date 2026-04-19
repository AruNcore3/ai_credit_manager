import os
import stripe
from sqlalchemy.orm import Session

from app.config import STRIPE_SECRET_KEY
from models.topup_attempt import TopUpAttempt
from services.credits_pricing import amount_cents_for_credits

stripe.api_key = STRIPE_SECRET_KEY

TOPUP_CURRENCY = os.getenv("TOPUP_CURRENCY", "usd").lower()
MIN_AMOUNT_BY_CURRENCY = {
    "usd": 50,  # $0.50 (cents)
    "inr": 50,  # Rs 0.50 (paise)
}


def create_topup_intent(
    db: Session,
    *,
    user_id: int,
    credits: int,
    idempotency_key: str,
):
    amount_cents = amount_cents_for_credits(credits)
    min_amount = MIN_AMOUNT_BY_CURRENCY.get(TOPUP_CURRENCY, 50)
    if amount_cents < min_amount:
        raise ValueError(
            f"Top-up amount is below Stripe minimum for {TOPUP_CURRENCY.upper()}."
        )

    attempt = TopUpAttempt(
        user_id=user_id,
        credits=credits,
        status="initiated",
        idempotency_key=idempotency_key,
    )
    db.add(attempt)
    db.flush()

    pi = stripe.PaymentIntent.create(
        amount=amount_cents,
        currency=TOPUP_CURRENCY,
        automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
        confirm=True,
        payment_method="pm_card_visa",
        metadata={
            "user_id": str(user_id),
            "topup_attempt_id": str(attempt.id),
            "credits": str(credits),
        },
        idempotency_key=idempotency_key,
    )

    attempt.stripe_payment_intent_id = pi.id
    db.commit()
    db.refresh(attempt)

    return attempt, pi, amount_cents
