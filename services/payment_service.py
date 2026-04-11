import stripe
from sqlalchemy.orm import Session
from app.config import STRIPE_SECRET_KEY
from models.topup_attempt import TopUpAttempt
from services.credits_pricing import amount_cents_for_credits

stripe.api_key = STRIPE_SECRET_KEY

def create_topup_intent(
    db: Session,
    *,
    user_id: int,
    credits: int,
    idempotency_key: str,
):
    amount_cents = amount_cents_for_credits(credits)

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
        currency="usd",
        automatic_payment_methods={"enabled": True},
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
