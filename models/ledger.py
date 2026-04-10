from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class LedgerEntryType(str, Enum):
    TOPUP = "topup"
    SPEND = "spend"
    ADJUSTMENT = "adjustment"
    REFUND = "refund"


class Ledger(Base):
    __tablename__ = "ledger"
    __table_args__ = (
        CheckConstraint("delta <> 0", name="ck_ledger_delta_nonzero"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    entry_type: Mapped[str] = mapped_column(String, nullable=False)
    reference: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)

    user = relationship("User", back_populates="ledger")

    def __repr__(self) -> str:
        return (
            f"Ledger(id={self.id!r}, user_id={self.user_id!r}, delta={self.delta!r}, "
            f"entry_type={self.entry_type!r}, reference={self.reference!r})"
        )


def record_ledger_entry(
    *,
    user_id: int,
    delta: int,
    entry_type: str,
    reference: Optional[str] = None,
) -> Ledger:
    if delta == 0:
        raise ValueError("delta must be non-zero")
    if not entry_type:
        raise ValueError("entry_type is required")

    return Ledger(
        user_id=user_id,
        delta=delta,
        entry_type=entry_type,
        reference=reference,
    )

