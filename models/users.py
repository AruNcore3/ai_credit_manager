from sqlalchemy.orm.session import Session
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class User(Base):
    __tablename__ = "users"
    id = Column[int](Integer, primary_key=True, index=True)
    username = Column[str](String, unique=True, index=True)
    email = Column[str](String, unique=True, index=True)
    password_hash = Column[str](String, nullable=False)

    is_active = Column[bool](Boolean, default=True)
    created_at = Column[datetime](DateTime, default=datetime.now)
    updated_at = Column[datetime](DateTime, default=datetime.now)
    wallet = relationship("Wallet", back_populates="user",uselist=False)
    ledger = relationship("Ledger", back_populates="user")

if __name__ == "__main__":
    pass
