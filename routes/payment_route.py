import uuid
import stripe
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from models.users import User
from schemas.wallet_schema import TopUpIntentRequest, TopUpIntentResponse
from services.payment_service import create_topup_intent

router = APIRouter(prefix="/payments", tags=["payments"])

@router.post("/topup-intent", response_model=TopUpIntentResponse)
def topup_intent(
    body: TopUpIntentRequest,
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    x_user_id: int = Header(alias="X-User-Id"),  # replace with auth later
):
    if body.credits <= 0:
        raise HTTPException(status_code=400, detail="credits must be > 0")
    user = db.query(User).filter(User.id == x_user_id).one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail=f"user {x_user_id} not found")

    key = idempotency_key or str(uuid.uuid4())
    try:
        attempt, pi, amount_cents = create_topup_intent(
            db,
            user_id=x_user_id,
            credits=body.credits,
            idempotency_key=key,
        )
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    except stripe.error.StripeError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"stripe error: {str(exc)}")

    return TopUpIntentResponse(
        attempt_id=attempt.id,
        client_secret=pi.client_secret,
        amount_cents=amount_cents,
        idempotency_key=key,
    )
