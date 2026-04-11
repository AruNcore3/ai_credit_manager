from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TopUpAttempt(Base):
    """
    One row per auto (or manual) top-up try, keyed by ``idempotency_key`` so the
    same logical top-up cannot be charged or credited twice under concurrency.
    """

    __tablename__ = "topup_attempts"
    __table_args__ = (
        CheckConstraint(
            "status IN ('initiated', 'paid', 'failed')",
            name="ck_topup_attempt_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    credits: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String, nullable=False, default="initiated", index=True
    )
    idempotency_key: Mapped[str] = mapped_column(
        String, nullable=False, unique=True, index=True
    )
    stripe_payment_intent_id: Mapped[Optional[str]] = mapped_column(
        String, nullable=True, index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, nullable=False
    )

    user = relationship("User", back_populates="topup_attempts")
