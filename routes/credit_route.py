from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.auth import get_current_user
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
    current_user: User = Depends(get_current_user),
):
    wallet = get_or_create_wallet(db, user_id=current_user.id)
    db.commit()
    return BalanceResponse(user_id=current_user.id, balance=wallet.balance)

@router.get("/ledger", response_model=list[LedgerItem])
def ledger(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(Ledger)
        .filter(Ledger.user_id == current_user.id)
        .order_by(Ledger.created_at.desc())
        .limit(100)
        .all()
    )
    return rows
