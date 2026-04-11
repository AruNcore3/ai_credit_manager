from __future__ import annotations

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# ✅ Avoid circular import
if TYPE_CHECKING:
    from app.models.user import User


class TopUpAttempt(Base):
    __tablename__ = "topup_attempts"

    __table_args__ = (
        CheckConstraint(
            "status IN ('initiated', 'paid', 'failed')",
            name="ck_topup_attempt_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    credits: Mapped[int] = mapped_column(nullable=False)

    status: Mapped[str] = mapped_column(
        String,
        default="initiated",
        nullable=False,
        index=True,
    )

    idempotency_key: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
        index=True,
    )

    stripe_payment_intent_id: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="topup_attempts",
    )                                                                                           
    