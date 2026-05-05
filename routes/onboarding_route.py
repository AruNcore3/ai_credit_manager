from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from schemas.users_schema import SignupRequest, SignupResponse
from services.tenant_service import signup_tenant_user

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.post("/signup", response_model=SignupResponse)
def signup(body: SignupRequest, db: Session = Depends(get_db)):
    try:
        account, user, key_row, raw_key = signup_tenant_user(
            db,
            account_name=body.account_name,
            username=body.username,
            email=body.email,
            password=body.password,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return SignupResponse(
        account_id=account.id,
        user_id=user.id,
        api_key=raw_key,
        key_prefix=key_row.key_prefix,
    )
