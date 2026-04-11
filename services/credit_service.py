from sqlalchemy.orm import Session
from models.topup_attempt import TopUpAttempt
from models.wallet import add_credits

def apply_paid_topup_once(db: Session, *, payment_intent_id: str) -> bool:
    attempt = (
        db.query(TopUpAttempt)
        .filter(TopUpAttempt.stripe_payment_intent_id == payment_intent_id)
        .one_or_none()
    )
    if attempt is None:
        return False
    if attempt.status == "paid":
        return False  # idempotent: already credited

    add_credits(
        db,
        user_id=attempt.user_id,
        amount=attempt.credits,
        entry_type="topup",
        reference=payment_intent_id,
    )
    attempt.status = "paid"
    db.commit()
    return True
