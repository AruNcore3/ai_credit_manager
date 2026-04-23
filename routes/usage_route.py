from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.auth import get_current_user
from app.database import get_db
from models.users import User
from schemas.usage_schema import UsageRecordRequest, UsageRecordResponse
from services.usage_service import record_usage

router = APIRouter(prefix="/v1/usage", tags=["usage"])

@router.post("/record", response_model=UsageRecordResponse)
def usage_record(
    body: UsageRecordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        result = record_usage(db=db, user_id=current_user.id, payload=body)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

        
