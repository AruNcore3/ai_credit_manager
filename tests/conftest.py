from sqlalchemy.orm.session import Session


import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure runtime config imports succeed in test mode.
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_dummy")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_dummy")
os.environ.setdefault("RATE_LIMIT_MAX_REQUESTS", "3")
os.environ.setdefault("RATE_LIMIT_WINDOW_SECONDS", "60")

from app.database import Base, get_db  # noqa: E402
from app.main import app, rate_limiter  # noqa: E402
from models.account import Account  # noqa: F401,E402
from models.ledger import Ledger  # noqa: F401,E402
from models.topup_attempt import TopUpAttempt  # noqa: F401,E402
from models.users import User  # noqa: F401,E402
from models.wallet import Wallet  # noqa: F401,E402


@pytest.fixture()
def test_db_session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker[Session](autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(test_db_session: Session) -> TestClient:
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    rate_limiter.reset()
    with TestClient(app) as test_client:
        yield test_client
    rate_limiter.reset()
    app.dependency_overrides.clear()
