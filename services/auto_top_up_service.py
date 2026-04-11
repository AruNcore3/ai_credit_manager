"""Auto top-up when wallet balance is low (Stripe direct charge) — expand later."""

from sqlalchemy.orm import Session


def maybe_auto_top_up(db: Session, user_id: int) -> bool:
    """
    Return True if a top-up was triggered and applied.

    Placeholder: wire Stripe PaymentIntent + ``models.wallet.add_credits`` here.
    """
    _ = (db, user_id)
    return False
