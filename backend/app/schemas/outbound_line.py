from pydantic import BaseModel, Field
from datetime import datetime


class OutboundLineBase(BaseModel):
    phone_number: str = Field(..., min_length=1, max_length=32)
    display_name: str = Field(..., min_length=1, max_length=255)
    is_active: bool = True


class OutboundLineCreate(OutboundLineBase):
    company_id: int


class OutboundLineUpdate(BaseModel):
    display_name: str | None = None
    is_active: bool | None = None


class OutboundLineOut(OutboundLineBase):
    id: int
    company_id: int
    created_at: datetime

    class Config:
        from_attributes = True
