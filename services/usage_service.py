import math
import os

from sqlalchemy.orm import Session
from models.ledger import Ledger
from models.wallet import InsufficientCreditsError, get_or_create_wallet, spend_credits
from schemas.usage_schema import UsageRecordRequest, UsageRecordResponse

INPUT_CREDIT_PER_1K = float(os.getenv("INPUT_CREDIT_PER_1K","1"))
OUTPUT_CREDIT_PER_1K = float(os.getenv("OUTPUT_CREDIT_PER_1K","2"))

def credit_for_usage(input_token:int,output_token:int) -> int:
    if input_token < 0 or output_token < 0:
        raise ValueError("token count must be >= 0")
    raw = (input_token/1000)*INPUT_CREDIT_PER_1K + (output_token/1000)*OUTPUT_CREDIT_PER_1K

    return max(1,math.ceil(raw)) if(input_token + output_token)>0 else 0

def record_usage( 
    db: Session,
     *,
    user_id: int, 
    payload: UsageRecordRequest, 
    ) -> UsageRecordResponse:

    reference = f"usage:{payload.event_id}"
    
    existing = (
        db.query(Ledger).filter(
            Ledger.user_id == user_id,
            Ledger.entry_type == "spend"
            Ledger.reference == reference,
        ).one_or_none()
    )
    wallet = get_or_create_wallet(db,user_id=user_id)

    if existing is not None:
        return UsageRecordResponse(
            event_id=payload.event_id,
            debited_credits=abs(existing.delta()),
            remaining_balance=wallet.balance,
            topup_required=False,
        )
    credit_to_debits = record_usage(payload.input_token,payload.output_token)
    if credit_to_debits == 0:
        return UsageRecordResponse(
            event_id=payload.event_id,
            debited_credits=0,
            remaining_balance=wallet.balance,
            topup_required="False",
        )
    try:
        wallet = spend_credits(
            db,
            user_id= user_id,
            amount=credit_to_debits,
            entry_type="spend",
            reference=reference,
        )
        db.commit()
        return UsageRecordResponse(
            event_id=payload.event_id,
            debited_credits=credit_to_debits,
            remaining_balance=wallet.balance,
            topup_required="False",
        )
    except InsufficientCreditsError:
        db.rollback()
        wallet = get_or_create_wallet(db,user_id=user_id)
        return UsageRecordResponse(
            event_id=payload.event_id,
            debited_credits=0,
            remaining_balance=wallet.balance,
            topup_required="True",
        )
