from __future__ import annotations

from sqlalchemy.orm import Session

from models.account import Account
from models.ledger import Ledger
from models.topup_attempt import TopUpAttempt
from models.users import User
from models.wallet import get_or_create_wallet
from services.reconcilation_service import reconile_initiated_topups


def _create_user(db: Session, user_id: int = 1) -> User:
    account = Account(name=f"account_{user_id}")
    db.add(account)
    db.flush()

    user = User(
        id=user_id,
        account_id=account.id,
        api_key=f"legacy-api-key-{user_id}",
        username=f"user_{user_id}",
        email=f"user_{user_id}@example.com",
        password_hash="test_hash",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_attempt(
    db: Session,
    *,
    user_id: int,
    credits: int = 5000,
    status: str = "initiated",
    payment_intent_id: str = "pi_test_1",
    idem: str = "idem_test_1",
) -> TopUpAttempt:
    attempt = TopUpAttempt(
        user_id=user_id,
        credits=credits,
        status=status,
        idempotency_key=idem,
        stripe_payment_intent_id=payment_intent_id,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


def test_reconciliation_succeeded_applies_credit_once(test_db_session: Session, monkeypatch):
    _create_user(test_db_session, user_id=1)
    attempt = _create_attempt(
        test_db_session,
        user_id=1,
        credits=5000,
        payment_intent_id="pi_success_1",
        idem="idem_success_1",
    )

    def fake_retrieve(payment_intent_id: str):
        assert payment_intent_id == "pi_success_1"
        return {"id": "pi_success_1", "status": "succeeded"}

    monkeypatch.setattr("services.reconcilation_service.stripe.PaymentIntent.retrieve", fake_retrieve)

    summary = reconile_initiated_topups(test_db_session, older_than_minutes=0)

    assert summary["checked"] == 1
    assert summary["applied"] == 1
    assert summary["already_paid"] == 0
    assert summary["failed"] == 0
    assert summary["pending"] == 0
    assert summary["error"] == 0

    test_db_session.refresh(attempt)
    assert attempt.status == "paid"

    wallet = get_or_create_wallet(test_db_session, user_id=1)
    assert wallet.balance == 5000

    rows = (
        test_db_session.query(Ledger)
        .filter(Ledger.user_id == 1, Ledger.entry_type == "topup", Ledger.reference == "pi_success_1")
        .all()
    )
    assert len(rows) == 1


def test_reconciliation_rerun_does_not_double_credit(test_db_session: Session, monkeypatch):
    _create_user(test_db_session, user_id=1)
    _create_attempt(
        test_db_session,
        user_id=1,
        credits=5000,
        payment_intent_id="pi_success_2",
        idem="idem_success_2",
    )

    def fake_retrieve(_: str):
        return {"id": "pi_success_2", "status": "succeeded"}

    monkeypatch.setattr("services.reconcilation_service.stripe.PaymentIntent.retrieve", fake_retrieve)

    first = reconile_initiated_topups(test_db_session, older_than_minutes=0)
    second = reconile_initiated_topups(test_db_session, older_than_minutes=0)

    assert first["applied"] == 1
    assert second["checked"] == 0

    wallet = get_or_create_wallet(test_db_session, user_id=1)
    assert wallet.balance == 5000

    rows = (
        test_db_session.query(Ledger)
        .filter(Ledger.user_id == 1, Ledger.entry_type == "topup", Ledger.reference == "pi_success_2")
        .all()
    )
    assert len(rows) == 1


def test_reconciliation_marks_failed_for_canceled_payment(test_db_session: Session, monkeypatch):
    _create_user(test_db_session, user_id=1)
    attempt = _create_attempt(
        test_db_session,
        user_id=1,
        credits=5000,
        payment_intent_id="pi_canceled_1",
        idem="idem_canceled_1",
    )

    def fake_retrieve(_: str):
        return {"id": "pi_canceled_1", "status": "canceled"}

    monkeypatch.setattr("services.reconcilation_service.stripe.PaymentIntent.retrieve", fake_retrieve)

    summary = reconile_initiated_topups(test_db_session, older_than_minutes=0)

    assert summary["failed"] == 1
    assert summary["error"] == 0

    test_db_session.refresh(attempt)
    assert attempt.status == "failed"

    wallet = get_or_create_wallet(test_db_session, user_id=1)
    assert wallet.balance == 0


def test_reconciliation_keeps_pending_intact(test_db_session: Session, monkeypatch):
    _create_user(test_db_session, user_id=1)
    attempt = _create_attempt(
        test_db_session,
        user_id=1,
        credits=5000,
        payment_intent_id="pi_pending_1",
        idem="idem_pending_1",
    )

    def fake_retrieve(_: str):
        return {"id": "pi_pending_1", "status": "processing"}

    monkeypatch.setattr("services.reconcilation_service.stripe.PaymentIntent.retrieve", fake_retrieve)

    summary = reconile_initiated_topups(test_db_session, older_than_minutes=0)

    assert summary["pending"] == 1
    assert summary["applied"] == 0
    assert summary["failed"] == 0
    assert summary["error"] == 0

    test_db_session.refresh(attempt)
    assert attempt.status == "initiated"


