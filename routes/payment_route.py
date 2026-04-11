import uuid
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
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

    key = idempotency_key or str(uuid.uuid4())
    attempt, pi, amount_cents = create_topup_intent(
        db,
        user_id=x_user_id,
        credits=body.credits,
        idempotency_key=key,
    )
    return TopUpIntentResponse(
        attempt_id=attempt.id,
        client_secret=pi.client_secret,
        amount_cents=amount_cents,
        idempotency_key=key,
    )
