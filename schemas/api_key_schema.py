from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ApiKeyCreateRequest(BaseModel):
    name: str


class ApiKeyCreateResponse(BaseModel):
    id: int
    name: str
    key_prefix: str
    api_key: str
    created_at: datetime


class ApiKeyItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    key_prefix: str
    created_at: datetime
    last_used_at: datetime | None
    revoked_at: datetime | None


class ApiKeyRotateResponse(BaseModel):
    id: int
    name: str
    key_prefix: str
    api_key: str
    created_at: datetime


class ApiKeyRevokeResponse(BaseModel):
    id: int
    revoked_at: datetime

