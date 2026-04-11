from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer,Boolean
from sqlalchemy.orm import Session, Mapped, mapped_column, relationship

from app.database import Base
from models.ledger import Ledger


class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    # auto top up settings
    auto_top_up_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    auto_top_up_amount: Mapped[int] = mapped_column(Integer, default=5000, nullable=False)
    auto_top_up_threshold: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    auto_top_up_daily_limit: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    auto_top_up_monthly: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
   
    user = relationship("User", back_populates="wallet")


class InsufficientCreditsError(ValueError):
    pass

    
def get_or_create_wallet(db: Session, *, user_id: int) -> Wallet:
    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).one_or_none()
    if wallet is not None:
        return wallet

    wallet = Wallet(user_id=user_id, balance=0)
    db.add(wallet)
    db.flush()
    return wallet


def add_credits(
    db: Session,
    *,
    user_id: int,
    amount: int,
    entry_type: str = "topup",
    reference: Optional[str] = None,
) -> Wallet:
    if amount <= 0:
        raise ValueError("amount must be > 0")

    wallet = get_or_create_wallet(db, user_id=user_id)
    wallet.balance += amount
    wallet.updated_at = datetime.now()

    db.add(
        Ledger(
            user_id=user_id,
            delta=amount,
            entry_type=entry_type,
            reference=reference,
        )
    )
    db.flush()
    return wallet


def spend_credits(
    db: Session,
    *,
    user_id: int,
    amount: int,
    entry_type: str = "spend",
    reference: Optional[str] = None,
    allow_negative: bool = False,
) -> Wallet:
    if amount <= 0:
        raise ValueError("amount must be > 0")

    wallet = get_or_create_wallet(db, user_id=user_id)
    if not allow_negative and wallet.balance < amount:
        raise InsufficientCreditsError("insufficient credits")

    wallet.balance -= amount
    wallet.updated_at = datetime.now()

    db.add(
        Ledger(
            user_id=user_id,
            delta=-amount,
            entry_type=entry_type,
            reference=reference,
        )
    )
    db.flush()
    return wallet

