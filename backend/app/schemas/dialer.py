from datetime import datetime
from pydantic import BaseModel, Field
from .phone_number import CallStatus


class DialerNumber(BaseModel):
    id: int
    phone_number: str


class DialerBatchOut(BaseModel):
    batch_id: str
    size_requested: int
    size_returned: int
    numbers: list[DialerNumber]


class NextBatchResponse(BaseModel):
    call_allowed: bool
    timezone: str = "Asia/Tehran"
    server_time: datetime
    schedule_version: int
    reason: str | None = None
    retry_after_seconds: int | None = None
    batch: DialerBatchOut | None = None


class DialerReport(BaseModel):
    number_id: int | None = Field(default=None, description="Optional when reporting by phone_number only")
    phone_number: str
    status: CallStatus
    reason: str | None = None
    attempted_at: datetime
    call_allowed: bool | None = None
