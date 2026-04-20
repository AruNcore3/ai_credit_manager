from datetime import datetime
from pydantic import BaseModel,ConfigDict

class UsageRecordRequest(BaseModel):
    event_id: str
    model: str
    input_token: int
    output_token: int

class UsageRecordResponse(BaseModel):
    event_id: str
    debited_credits: int
    remaining_balance: int
    topup_required: bool

