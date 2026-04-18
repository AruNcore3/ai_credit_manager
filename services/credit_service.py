from sqlalchemy.orm import Session
from models.topup_attempt import TopUpAttempt
from models.wallet import add_credits

def apply_paid_topup_once(
    db: Session,
    *,
    attempt_id: int | None = None,
    payment_intent_id: str | None = None,
) -> bool:
    if attempt_id is not None:
        attempt = (
            db.query(TopUpAttempt)
            .filter(TopUpAttempt.id == attempt_id)
            .one_or_none()
        )
    elif payment_intent_id:
        attempt = (
            db.query(TopUpAttempt)
            .filter(TopUpAttempt.stripe_payment_intent_id == payment_intent_id)
            .one_or_none()
        )
    else:
        raise ValueError("attempt_id or payment_intent_id is required")

    if attempt is None:
        return False
    if attempt.status == "paid":
        return False  # idempotent: already credited

    reference = payment_intent_id or attempt.stripe_payment_intent_id
    add_credits(
        db,
        user_id=attempt.user_id,
        amount=attempt.credits,
        entry_type="topup",
        reference=reference,
    )

    if payment_intent_id and not attempt.stripe_payment_intent_id:
        attempt.stripe_payment_intent_id = payment_intent_id

    attempt.status = "paid"
    db.commit()
    return True
