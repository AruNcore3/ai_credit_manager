import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.database import get_db
from models.account import Account
from models.api_key import ApiKey
from models.webhook_delivery import WebhookDelivery
from models.users import User
from schemas.api_key_schema import ApiKeyItem
from schemas.users_schema import AccountAdminItem, AccountAdminUpdateRequest, CreditAdjustmentRequest
from services.api_key_service import revoke_api_key
from services.audit_service import log_audit_event
from services.tenant_service import admin_credit_adjustment
from services.webhook_processor_service import process_stripe_event
from services.webhook_reliability_service import mark_processed, mark_replayed

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/accounts", response_model=list[AccountAdminItem])
def list_accounts(db: Session = Depends(get_db)):
    return db.query(Account).order_by(Account.created_at.desc()).all()


@router.patch("/accounts/{account_id}", response_model=AccountAdminItem)
def update_account(account_id: int, body: AccountAdminUpdateRequest, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.id == account_id).one_or_none()
    if account is None:
        raise HTTPException(status_code=404, detail="account not found")

    if body.plan_name is not None:
        account.plan_name = body.plan_name
    if body.monthly_credit_quota is not None:
        account.monthly_credit_quota = body.monthly_credit_quota
    if body.is_suspended is not None:
        account.is_suspended = body.is_suspended

    db.commit()
    log_audit_event(
        db,
        actor_type="admin",
        actor_id="admin_token",
        account_id=account.id,
        action="admin.account.update",
        target_type="account",
        target_id=str(account.id),
        metadata={
            "plan_name": account.plan_name,
            "monthly_credit_quota": account.monthly_credit_quota,
            "is_suspended": account.is_suspended,
        },
    )
    db.commit()
    db.refresh(account)
    return account


@router.post("/users/{user_id}/credits")
def adjust_user_credits(user_id: int, body: CreditAdjustmentRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")

    admin_credit_adjustment(db, user_id=user_id, amount=body.amount, reason=body.reason)
    log_audit_event(
        db,
        actor_type="admin",
        actor_id="admin_token",
        account_id=user.account_id,
        action="admin.credits.adjust",
        target_type="user",
        target_id=str(user.id),
        metadata={"amount": body.amount, "reason": body.reason},
    )
    db.commit()
    return {"ok": True}


@router.get("/accounts/{account_id}/keys", response_model=list[ApiKeyItem])
def list_account_keys(account_id: int, db: Session = Depends(get_db)):
    rows = (
        db.query(ApiKey)
        .join(User, User.id == ApiKey.user_id)
        .filter(User.account_id == account_id)
        .order_by(ApiKey.created_at.desc())
        .all()
    )
    return rows


@router.post("/keys/{key_id}/revoke")
def revoke_any_key(key_id: int, db: Session = Depends(get_db)):
    row = db.query(ApiKey).filter(ApiKey.id == key_id).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="api key not found")

    revoke_api_key(db, user_id=row.user_id, key_id=key_id)
    log_audit_event(
        db,
        actor_type="admin",
        actor_id="admin_token",
        action="admin.api_key.revoke",
        target_type="api_key",
        target_id=str(key_id),
    )
    db.commit()
    return {"ok": True}


@router.get("/webhooks/dlq")
def list_webhook_dlq(status: str = "dead_letter", limit: int = 100, db: Session = Depends(get_db)):
    rows = (
        db.query(WebhookDelivery)
        .filter(WebhookDelivery.status == status)
        .order_by(WebhookDelivery.updated_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": row.id,
            "provider": row.provider,
            "event_id": row.event_id,
            "event_type": row.event_type,
            "status": row.status,
            "attempts": row.attempts,
            "max_attempts": row.max_attempts,
            "next_retry_at": row.next_retry_at.isoformat() if row.next_retry_at else None,
            "error_message": row.error_message,
            "updated_at": row.updated_at.isoformat(),
        }
        for row in rows
    ]


@router.post("/webhooks/dlq/{delivery_id}/replay")
def replay_webhook_delivery(delivery_id: int, db: Session = Depends(get_db)):
    row = db.query(WebhookDelivery).filter(WebhookDelivery.id == delivery_id).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="webhook delivery not found")

    try:
        payload = json.loads(row.payload_json)
    except Exception:
        raise HTTPException(status_code=400, detail="webhook payload is invalid")

    try:
        process_stripe_event(db, payload)
        mark_processed(db, row.event_id)
        mark_replayed(db, event_id=row.event_id)
        log_audit_event(
            db,
            actor_type="admin",
            actor_id="admin_token",
            action="admin.webhook.replay",
            target_type="webhook_delivery",
            target_id=str(row.id),
            metadata={"event_id": row.event_id, "event_type": row.event_type},
        )
        db.commit()
        return {"ok": True, "status": "replayed"}
    except Exception as exc:
        db.rollback()
        row = db.query(WebhookDelivery).filter(WebhookDelivery.id == delivery_id).one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail="webhook delivery not found")
        row.error_message = str(exc)[:2000]
        row.status = "dead_letter"
        db.add(row)
        db.commit()
        raise HTTPException(status_code=500, detail=f"replay failed: {str(exc)}")
