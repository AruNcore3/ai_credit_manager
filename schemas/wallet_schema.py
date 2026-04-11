from pydantic import BaseModel

class TopUpIntentRequest(BaseModel):
    credits: int

class TopUpIntentResponse(BaseModel):
    attempt_id: int
    client_secret: str
    amount_cents: int
    idempotency_key: str

class BalanceResponse(BaseModel):
    user_id: int
    balance: int
