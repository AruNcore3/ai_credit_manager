from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy.orm import Session

import routes.webhook_route as webhook_route
import services.payment_service as payment_service
from models.ledger import Ledger
from models.topup_attempt import TopUpAttempt
from models.users import User


def _create_user(db: Session, user_id: int = 1) -> User:
    user = User(
        id=user_id,
        username=f"user_{user_id}",
        email=f"user_{user_id}@example.com",
        password_hash="test_hash",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_topup_intent_success(client, test_db_session: Session, monkeypatch: pytest.MonkeyPatch):
    _create_user(test_db_session, user_id=1)

    class FakePaymentIntent:
        id = "pi_test_123"
        client_secret = "pi_test_123_secret_abc"

    def fake_payment_intent_create(**kwargs: Any):
        assert kwargs["amount"] == 500
        assert kwargs["currency"] == "usd"
        return FakePaymentIntent()

    monkeypatch.setattr(payment_service.stripe.PaymentIntent, "create", fake_payment_intent_create)

    response = client.post(
        "/payments/topup-intent",
        headers={"X-User-Id": "1", "Idempotency-Key": "idem-key-1"},
        json={"credits": 5000},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["idempotency_key"] == "idem-key-1"
    assert payload["amount_cents"] == 500
    assert payload["client_secret"] == "pi_test_123_secret_abc"

    attempt = test_db_session.query(TopUpAttempt).filter_by(id=payload["attempt_id"]).one_or_none()
    assert attempt is not None
    assert attempt.status == "initiated"
    assert attempt.stripe_payment_intent_id == "pi_test_123"


def test_topup_intent_invalid_credits(client, test_db_session: Session):
    _create_user(test_db_session, user_id=1)

    response = client.post(
        "/payments/topup-intent",
        headers={"X-User-Id": "1"},
        json={"credits": 0},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "credits must be > 0"


def test_topup_intent_requires_user_header(client):
    response = client.post("/payments/topup-intent", json={"credits": 5000})
    assert response.status_code == 422


def test_balance_defaults_to_zero(client, test_db_session: Session):
    _create_user(test_db_session, user_id=1)
    response = client.get("/credits/balance", headers={"X-User-Id": "1"})
    assert response.status_code == 200
    assert response.json() == {"user_id": 1, "balance": 0}


def test_webhook_succeeded_applies_credit_once(client, test_db_session: Session, monkeypatch: pytest.MonkeyPatch):
    _create_user(test_db_session, user_id=1)
    attempt = TopUpAttempt(
        user_id=1,
        credits=5000,
        status="initiated",
        idempotency_key="idem-key-webhook",
        stripe_payment_intent_id="pi_success_1",
    )
    test_db_session.add(attempt)
    test_db_session.commit()

    def fake_construct_event(payload, sig_header, secret):  # noqa: ANN001
        assert sig_header == "test_sig"
        return {
            "type": "payment_intent.succeeded",
            "data": {"object": {"id": "pi_success_1"}},
        }

    monkeypatch.setattr(webhook_route.stripe.Webhook, "construct_event", fake_construct_event)

    first = client.post(
        "/webhooks/stripe",
        headers={"Stripe-Signature": "test_sig"},
        content=b"{}",
    )
    assert first.status_code == 200

    second = client.post(
        "/webhooks/stripe",
        headers={"Stripe-Signature": "test_sig"},
        content=b"{}",
    )
    assert second.status_code == 200

    balance = client.get("/credits/balance", headers={"X-User-Id": "1"})
    assert balance.status_code == 200
    assert balance.json()["balance"] == 5000

    ledger = client.get("/credits/ledger", headers={"X-User-Id": "1"})
    assert ledger.status_code == 200
    assert len(ledger.json()) == 1


def test_webhook_invalid_signature_returns_400(client, monkeypatch: pytest.MonkeyPatch):
    def fake_construct_event(payload, sig_header, secret):  # noqa: ANN001
        raise ValueError("bad signature")

    monkeypatch.setattr(webhook_route.stripe.Webhook, "construct_event", fake_construct_event)

    response = client.post(
        "/webhooks/stripe",
        headers={"Stripe-Signature": "bad_sig"},
        content=b"{}",
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "invalid webhook signature"


def test_ledger_endpoint_returns_rows(client, test_db_session: Session):
    _create_user(test_db_session, user_id=1)
    test_db_session.add(
        Ledger(
            user_id=1,
            delta=250,
            entry_type="adjustment",
            reference="manual",
        )
    )
    test_db_session.commit()

    response = client.get("/credits/ledger", headers={"X-User-Id": "1"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["delta"] == 250
