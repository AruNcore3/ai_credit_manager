from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer,String,Boolean
from sqlalchemy.orm import Session, Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(
        String, unique=True, index=True, nullable=True
    )
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    wallet = relationship("Wallet", back_populates="user", uselist=False)
    ledger = relationship("Ledger", back_populates="user")
    topup_attempts = relationship("TopUpAttempt", back_populates="user")

if __name__ == "__main__":
    pass
