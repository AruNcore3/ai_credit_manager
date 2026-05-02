import uuid
import logging
import stripe
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from app.auth import get_current_user
from app.database import get_db
from models.users import User
from schemas.wallet_schema import TopUpIntentRequest, TopUpIntentResponse
from services.payment_service import create_topup_intent

router = APIRouter(prefix="/payments", tags=["payments"])
logger = logging.getLogger(__name__)

@router.post("/topup-intent", response_model=TopUpIntentResponse)
def topup_intent(
    body: TopUpIntentRequest,
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user),
):
    if body.credits <= 0:
        raise HTTPException(status_code=400, detail="credits must be > 0")

    key = idempotency_key or str(uuid.uuid4())
    try:
        attempt, pi, amount_cents = create_topup_intent(
            db,
            user_id=current_user.id,
            credits=body.credits,
            idempotency_key=key,
        )
    except ValueError as exc:
        db.rollback()
        logger.warning(
            "topup_intent_rejected user_id=%s credits=%s reason=%s",
            current_user.id,
            body.credits,
            str(exc),
        )
        raise HTTPException(status_code=400, detail=str(exc))
    except stripe.error.StripeError as exc:
        db.rollback()
        logger.error(
            "topup_intent_stripe_error user_id=%s credits=%s idempotency_key=%s error=%s",
            current_user.id,
            body.credits,
            key,
            str(exc),
        )
        raise HTTPException(status_code=400, detail=f"stripe error: {str(exc)}")

    return TopUpIntentResponse(
        attempt_id=attempt.id,
        client_secret=pi.client_secret,
        amount_cents=amount_cents,
        idempotency_key=key,
    )
