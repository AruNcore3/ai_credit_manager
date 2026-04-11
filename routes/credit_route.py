from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from app.database import get_db
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
    wallet = get_or_create_wallet(db, user_id=x_user_id)
    db.commit()
    return BalanceResponse(user_id=x_user_id, balance=wallet.balance)

@router.get("/ledger", response_model=list[LedgerItem])
def ledger(
    db: Session = Depends(get_db),
    x_user_id: int = Header(alias="X-User-Id"),
):
    rows = (
        db.query(Ledger)
        .filter(Ledger.user_id == x_user_id)
        .order_by(Ledger.created_at.desc())
        .limit(100)
        .all()
    )
    return rows
