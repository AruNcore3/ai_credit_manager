from fastapi import APIRouter,Depends,HTTPException
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

from services.api_key_service import revoke_api_key
from services.api_key_service import (
    create_api_key,
    list_api_keys,
    revoke_api_key,
    rotate_api_key,
)

router = APIRouter(prefix="api-keys",tags=["api-keys"])

@router.post("",response_model=ApiKeyCreateResponse)
def create_key(
    body:ApiKeyCreateRequest,
    db:Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        row = revoke_api_key(db,user_id=current_user.id,name=body.name)
    except ValueError as exc:
        raise HTTPException(status_code=400, details=str(exc))

    return ApiKeyCreateResponse(
        id=row.id,
        name=row.name,
        key_prefix=row.key_prefix,
        api_key=raw_key,
        created_at=row.created_at,
    )

@router.get("",response_model=list[ApiKeyItem])
def list_keys(
    db:Session = Depends(get_db),
    current_user:User = Depends(get_current_user),
):
    rows = list_api_keys(db,user_id=current_user.id)
    return rows

@router.post(f"/{key_id}/revoke", response_model=ApiKeyRevokeResponse)
def revoke_key(
    key_id:int,
    db:Session = Depends(get_db),
    current_user:User = Depends(get_current_user),
):
    try:
        row = revoke_api_key(db,user_id=current_user.id,key_id=key_id)
    except ValueError:
        raise HTTPException(status_code=404,detail="api key not found")

    return ApiKeyCreateResponse(
        id=row.id,
        revoked_at = row.revoked_at,
    )

@router.post(f"/{key_id}/rotate", response_model=ApiKeyRotateResponse)
def rotate_key(
    key_id:int,
    db:Session = Depends(get_db),
    current_user:User = Depends(get_current_user),
):
    try:
        row,raw_key = rotate_api_key(db,user_id=current_user.id,key_id=key_id)
    except ValueError:
        raise HTTPException(staus_code=404,detail="api key not found")

    return ApiKeyRotateResponse(
        id=row.id,
        name=row.name,
        key_prefix=row.key_prefix,
        api_key=raw_key,
        created_at=row.created_at,
    )

