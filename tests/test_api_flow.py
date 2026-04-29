from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy.orm import Session

import routes.webhook_route as webhook_route
import services.payment_service as payment_service
from app import rate_limit
from models.account import Account
from models.api_key import ApiKey
from models.ledger import Ledger
from models.topup_attempt import TopUpAttempt
from models.users import User
from models.wallet import add_credits
from utils.api_keys import get_key_prefix, hash_api_key


def _create_user(
    db: Session,
    user_id: int = 1,
    *,
    api_key: str | None = None,
) -> User:
    raw_api_key = api_key or f"test-api-key-{user_id}"
    account = Account(name=f"account_{user_id}")
    db.add(account)
    db.flush()

    user = User(
        id=user_id,
        account_id=account.id,
        api_key=raw_api_key,
        username=f"user_{user_id}",
        email=f"user_{user_id}@example.com",
        password_hash="test_hash",
        is_active=True,
    )
    db.add(user)
    db.flush()

    db.add(
        ApiKey(
            user_id=user.id,
            name=f"default_{user_id}",
            key_prefix=get_key_prefix(raw_api_key),
            key_hash=hash_api_key(raw_api_key),
        )
    )
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
        "/v1/payments/topup-intent",
        headers={"X-API-Key": "test-api-key-1", "Idempotency-Key": "idem-key-1"},
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
        "/v1/payments/topup-intent",
        headers={"X-API-Key": "test-api-key-1"},
        json={"credits": 0},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "credits must be > 0"


def test_topup_intent_requires_api_key(client):
    response = client.post("/v1/payments/topup-intent", json={"credits": 5000})
    assert response.status_code == 401
    assert response.json()["detail"] == "missing API key"


def test_balance_defaults_to_zero(client, test_db_session: Session):
    _create_user(test_db_session, user_id=1)
    response = client.get("/v1/credits/balance", headers={"X-API-Key": "test-api-key-1"})
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
        "/v1/webhooks/stripe",
        headers={"Stripe-Signature": "test_sig"},
        content=b"{}",
    )
    assert first.status_code == 200

    second = client.post(
        "/v1/webhooks/stripe",
        headers={"Stripe-Signature": "test_sig"},
        content=b"{}",
    )
    assert second.status_code == 200

    balance = client.get("/v1/credits/balance", headers={"X-API-Key": "test-api-key-1"})
    assert balance.status_code == 200
    assert balance.json()["balance"] == 5000

    ledger = client.get("/v1/credits/ledger", headers={"X-API-Key": "test-api-key-1"})
    assert ledger.status_code == 200
    assert len(ledger.json()) == 1


def test_webhook_invalid_signature_returns_400(client, monkeypatch: pytest.MonkeyPatch):
    def fake_construct_event(payload, sig_header, secret):  # noqa: ANN001
        raise ValueError("bad signature")

    monkeypatch.setattr(webhook_route.stripe.Webhook, "construct_event", fake_construct_event)

    response = client.post(
        "/v1/webhooks/stripe",
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

    response = client.get("/v1/credits/ledger", headers={"X-API-Key": "test-api-key-1"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["delta"] == 250


def test_usage_record_debits_credits_and_returns_balance(client, test_db_session: Session):
    _create_user(test_db_session, user_id=1)
    add_credits(test_db_session, user_id=1, amount=500, reference="seed")
    test_db_session.commit()

    response = client.post(
        "/v1/usage/record",
        headers={"X-API-Key": "test-api-key-1"},
        json={
            "event_id": "evt_usage_1",
            "model": "gpt-test",
            "input_token": 1000,
            "output_token": 1000,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["event_id"] == "evt_usage_1"
    assert body["debited_credits"] == 3
    assert body["remaining_balance"] == 497
    assert body["topup_required"] is False


def test_usage_record_is_idempotent_by_event_id(client, test_db_session: Session):
    _create_user(test_db_session, user_id=1)
    add_credits(test_db_session, user_id=1, amount=20, reference="seed")
    test_db_session.commit()

    payload = {
        "event_id": "evt_usage_2",
        "model": "gpt-test",
        "input_token": 1000,
        "output_token": 1000,
    }
    headers = {"X-API-Key": "test-api-key-1"}

    first = client.post("/v1/usage/record", headers=headers, json=payload)
    second = client.post("/v1/usage/record", headers=headers, json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["debited_credits"] == 3
    assert second.json()["debited_credits"] == 3
    assert second.json()["remaining_balance"] == 17
    assert second.json()["topup_required"] is False

    spend_rows = (
        test_db_session.query(Ledger)
        .filter(Ledger.user_id == 1, Ledger.entry_type == "spend", Ledger.reference == "usage:evt_usage_2")
        .all()
    )
    assert len(spend_rows) == 1


def test_usage_record_zero_tokens_no_debit(client, test_db_session: Session):
    _create_user(test_db_session, user_id=1)

    response = client.post(
        "/v1/usage/record",
        headers={"X-API-Key": "test-api-key-1"},
        json={
            "event_id": "evt_usage_3",
            "model": "gpt-test",
            "input_token": 0,
            "output_token": 0,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["debited_credits"] == 0
    assert body["remaining_balance"] == 0
    assert body["topup_required"] is False

    spend_rows = (
        test_db_session.query(Ledger)
        .filter(Ledger.user_id == 1, Ledger.entry_type == "spend", Ledger.reference == "usage:evt_usage_3")
        .all()
    )
    assert len(spend_rows) == 0


def test_legacy_route_returns_deprecation_header(client, test_db_session: Session):
    _create_user(test_db_session, user_id=1)
    response = client.get("/credits/balance", headers={"X-API-Key": "test-api-key-1"})
    assert response.status_code == 200
    assert response.headers.get("Deprecation") == "true"


def test_usage_record_insufficient_credits_returns_topup_required(client, test_db_session: Session):
    _create_user(test_db_session, user_id=1)

    response = client.post(
        "/v1/usage/record",
        headers={"X-API-Key": "test-api-key-1"},
        json={
            "event_id": "evt_usage_4",
            "model": "gpt-test",
            "input_token": 1500,
            "output_token": 1500,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["debited_credits"] == 0
    assert body["remaining_balance"] == 0
    assert body["topup_required"] is True

    spend_rows = (
        test_db_session.query(Ledger)
        .filter(Ledger.user_id == 1, Ledger.entry_type == "spend", Ledger.reference == "usage:evt_usage_4")
        .all()
    )
    assert len(spend_rows) == 0

def test_api_keys_create_and_list(client, test_db_session: Session):
    _create_user(test_db_session, user_id=1)

    create_res = client.post(
        "/v1/api-keys",
        headers={"X-API-Key": "test-api-key-1"},
        json={"name": "prod-key"},
    )
    assert create_res.status_code == 200
    created = create_res.json()
    assert created["name"] == "prod-key"
    assert created["api_key"].startswith("ak_live_")
    assert created["key_prefix"]
    assert created["id"]

    list_res = client.get("/v1/api-keys", headers={"X-API-Key": "test-api-key-1"})
    assert list_res.status_code == 200
    items = list_res.json()
    assert any(item["id"] == created["id"] for item in items)
    assert all("api_key" not in item for item in items)  # raw keys must never be listed


def test_api_keys_revoke(client, test_db_session: Session):
    _create_user(test_db_session, user_id=1)

    create_res = client.post(
        "/v1/api-keys",
        headers={"X-API-Key": "test-api-key-1"},
        json={"name": "revoke-me"},
    )
    key_id = create_res.json()["id"]

    revoke_res = client.post(
        f"/v1/api-keys/{key_id}/revoke",
        headers={"X-API-Key": "test-api-key-1"},
    )
    assert revoke_res.status_code == 200
    body = revoke_res.json()
    assert body["id"] == key_id
    assert body["revoked_at"] is not None


def test_api_keys_rotate(client, test_db_session: Session):
    _create_user(test_db_session, user_id=1)

    create_res = client.post(
        "/v1/api-keys",
        headers={"X-API-Key": "test-api-key-1"},
        json={"name": "rotate-me"},
    )
    old_key = create_res.json()["api_key"]
    old_id = create_res.json()["id"]

    rotate_res = client.post(
        f"/v1/api-keys/{old_id}/rotate",
        headers={"X-API-Key": "test-api-key-1"},
    )
    assert rotate_res.status_code == 200
    rotated = rotate_res.json()
    new_key = rotated["api_key"]

    assert new_key.startswith("ak_live_")
    assert new_key != old_key
    assert rotated["id"] != old_id  # rotate creates new row in current service behavior

    old_auth = client.get("/v1/credits/balance", headers={"X-API-Key": old_key})
    assert old_auth.status_code == 401

    new_auth = client.get("/v1/credits/balance", headers={"X-API-Key": new_key})
    assert new_auth.status_code == 200


def test_rate_limiting_returns_429_after_limit(client, test_db_session: Session):
    _create_user(test_db_session, user_id=1)
    headers = {"X-API-Key": "test-api-key-1"}

    first = client.get("/v1/credits/balance", headers=headers)
    second = client.get("/v1/credits/balance", headers=headers)
    third = client.get("/v1/credits/balance", headers=headers)
    fourth = client.get("/v1/credits/balance", headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 200
    assert fourth.status_code == 429
    assert fourth.json()["detail"] == "rate limit exceeded"
    assert fourth.headers["X-RateLimit-Limit"] == "3"
    assert fourth.headers["X-RateLimit-Remaining"] == "0"
    assert int(fourth.headers["Retry-After"]) >= 1


def test_rate_limiting_resets_after_window(client, test_db_session: Session, monkeypatch: pytest.MonkeyPatch):
    _create_user(test_db_session, user_id=1)
    headers = {"X-API-Key": "test-api-key-1"}

    fake_time = {"now": 1000.0}

    def _time() -> float:
        return fake_time["now"]

    monkeypatch.setattr(rate_limit.time, "time", _time)

    for _ in range(3):
        ok = client.get("/v1/credits/balance", headers=headers)
        assert ok.status_code == 200

    blocked = client.get("/v1/credits/balance", headers=headers)
    assert blocked.status_code == 429

    fake_time["now"] += 61
    allowed_again = client.get("/v1/credits/balance", headers=headers)
    assert allowed_again.status_code == 200


def test_rate_limiting_is_isolated_per_api_key(client, test_db_session: Session):
    _create_user(test_db_session, user_id=1, api_key="test-api-key-1")
    _create_user(test_db_session, user_id=2, api_key="test-api-key-2")

    headers_one = {"X-API-Key": "test-api-key-1"}
    headers_two = {"X-API-Key": "test-api-key-2"}

    for _ in range(3):
        assert client.get("/v1/credits/balance", headers=headers_one).status_code == 200

    blocked = client.get("/v1/credits/balance", headers=headers_one)
    assert blocked.status_code == 429

    unaffected = client.get("/v1/credits/balance", headers=headers_two)
    assert unaffected.status_code == 200
