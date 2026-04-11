"""Step 3: single place for how many credits cost how much (Stripe uses cents)."""

from __future__ import annotations

import os

# Default pack size in credits (override via env if needed).
DEFAULT_TOPUP_CREDITS: int = int(os.getenv("DEFAULT_TOPUP_CREDITS", "5000"))

# Price for exactly DEFAULT_TOPUP_CREDITS credits, in smallest currency unit (e.g. USD cents).
# Default 500 cents = USD $5.00 for 5,000 credits (same per-credit rate as the old 10k/$10 example).
_DEFAULT_CENTS_PER_PACK: int = int(
    os.getenv("CENTS_PER_TOPUP_PACK", os.getenv("CENTS_PER_10K_CREDITS", "500"))
)


def amount_cents_for_credits(credits: int) -> int:
    """
    Linear pricing: ``(credits / DEFAULT_TOPUP_CREDITS) * CENTS_PER_TOPUP_PACK``,
    rounded down to whole cents.
    """
    if credits <= 0:
        raise ValueError("credits must be > 0")
    return (credits * _DEFAULT_CENTS_PER_PACK) // DEFAULT_TOPUP_CREDITS
