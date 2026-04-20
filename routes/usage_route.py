from fastapi import APIRouter,Header,HTTPException,Depends
from sqlalchemy.orm import Session
from sqlalchemy.schema import DropColumnComment
from app.database import get_db
from schemas.usage_schema import UsageRecordRequest,UsageRecordResponse
from services.usage_service import record_usage

router = APIRouter(prefix = "/usage",tags = ["usage"])

@router.post("/record",response_model=UsageRecordResponse)
def usage_record(
    body:UsageRecordRequest,
    db:Session = Depends(get_db),
    x_user_id: int = Header(alias="X_User_id"),
):
    try:
        result = usage_record(db=db,x_user_id=x_user_id,payload=body)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400,detail=str(exc))

        