from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SignupRequest(BaseModel):
    account_name: str = Field(min_length=3, max_length=80)
    username: str = Field(min_length=3, max_length=80)
    email: str
    password: str = Field(min_length=8, max_length=256)


class SignupResponse(BaseModel):
    account_id: int
    user_id: int
    api_key: str
    key_prefix: str


class AccountAdminItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    plan_name: str
    monthly_credit_quota: int
    period_spend_credits: int
    is_suspended: bool
    created_at: datetime


class AccountAdminUpdateRequest(BaseModel):
    plan_name: str | None = None
    monthly_credit_quota: int | None = Field(default=None, ge=0)
    is_suspended: bool | None = None


class CreditAdjustmentRequest(BaseModel):
    amount: int = Field(gt=0)
    reason: str = Field(min_length=3, max_length=120)
