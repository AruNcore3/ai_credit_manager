from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from models.users import User
from schemas.api_key_schema import (
    ApiKeyCreateRequest,
    ApiKeyCreateResponse,
    ApiKeyItem,
    ApiKeyRevokeResponse,
    ApiKeyRotateResponse,
)
from services.api_key_service import (
    create_api_key,
    list_api_keys,
    revoke_api_key,
    rotate_api_key,
)
from services.audit_service import log_audit_event

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


@router.post("", response_model=ApiKeyCreateResponse)
def create_key(
    body: ApiKeyCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        row, raw_key = create_api_key(db, user_id=current_user.id, name=body.name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    log_audit_event(
        db,
        actor_type="user",
        actor_id=str(current_user.id),
        account_id=current_user.account_id,
        action="api_key.create",
        target_type="api_key",
        target_id=str(row.id),
        metadata={"name": row.name, "key_prefix": row.key_prefix},
    )
    db.commit()

    return ApiKeyCreateResponse(
        id=row.id,
        name=row.name,
        key_prefix=row.key_prefix,
        api_key=raw_key,
        created_at=row.created_at,
    )
@router.get("", response_model=list[ApiKeyItem])
def list_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = list_api_keys(db, user_id=current_user.id)
    return rows


@router.post("/{key_id}/revoke", response_model=ApiKeyRevokeResponse)
def revoke_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        row = revoke_api_key(db, user_id=current_user.id, key_id=key_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="api key not found")
    log_audit_event(
        db,
        actor_type="user",
        actor_id=str(current_user.id),
        account_id=current_user.account_id,
        action="api_key.revoke",
        target_type="api_key",
        target_id=str(row.id),
    )
    db.commit()

    return ApiKeyRevokeResponse(
        id=row.id,
        revoked_at=row.revoked_at,
    )


@router.post("/{key_id}/rotate", response_model=ApiKeyRotateResponse)
def rotate_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        row, raw_key = rotate_api_key(db, user_id=current_user.id, key_id=key_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="api key not found")
    log_audit_event(
        db,
        actor_type="user",
        actor_id=str(current_user.id),
        account_id=current_user.account_id,
        action="api_key.rotate",
        target_type="api_key",
        target_id=str(row.id),
    )
    db.commit()

    return ApiKeyRotateResponse(
        id=row.id,
        name=row.name,
        key_prefix=row.key_prefix,
        api_key=raw_key,
        created_at=row.created_at,
    )
