from fastapi import APIRouter, Depends, Header
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from models.users import User
from models.wallet import get_or_create_wallet
from models.ledger import Ledger
from schemas.wallet_schema import BalanceResponse
from schemas.ledger_schema import LedgerItem

router = APIRouter(prefix="/credits", tags=["credits"])

@router.get("/balance", response_model=BalanceResponse)
def balance(
    db: Session = Depends(get_db),
    x_user_id: int = Header(alias="X-User-Id"),
):
    user = db.query(User).filter(User.id == x_user_id).one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail=f"user {x_user_id} not found")
    wallet = get_or_create_wallet(db, user_id=x_user_id)
    db.commit()
    return BalanceResponse(user_id=x_user_id, balance=wallet.balance)

@router.get("/ledger", response_model=list[LedgerItem])
def ledger(
    db: Session = Depends(get_db),
    x_user_id: int = Header(alias="X-User-Id"),
):
    user = db.query(User).filter(User.id == x_user_id).one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail=f"user {x_user_id} not found")
    rows = (
        db.query(Ledger)
        .filter(Ledger.user_id == x_user_id)
        .order_by(Ledger.created_at.desc())
        .limit(100)
        .all()
    )
    return rows
