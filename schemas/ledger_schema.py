from datetime import datetime
from pydantic import BaseModel,ConfigDict

class LedgerItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    delta: int
    entry_type: str
    reference: str | None
    created_at: datetime
