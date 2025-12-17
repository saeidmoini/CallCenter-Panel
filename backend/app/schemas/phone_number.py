from datetime import datetime
from pydantic import BaseModel, Field
from ..models.phone_number import CallStatus


class PhoneNumberCreate(BaseModel):
    phone_numbers: list[str] = Field(..., description="List of phone numbers to enqueue")


class PhoneNumberStatusUpdate(BaseModel):
    status: CallStatus
    note: str | None = None


class PhoneNumberOut(BaseModel):
    id: int
    phone_number: str
    status: CallStatus
    total_attempts: int
    last_attempt_at: datetime | None
    last_status_change_at: datetime | None
    assigned_at: datetime | None
    assigned_batch_id: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PhoneNumberImportResponse(BaseModel):
    inserted: int
    duplicates: int
    invalid: int
    invalid_samples: list[str] = []


class PhoneNumberStatsResponse(BaseModel):
    total: int


class PhoneNumberBulkAction(BaseModel):
    action: str = Field(..., pattern="^(update_status|reset|delete)$")
    status: CallStatus | None = None
    note: str | None = None
    ids: list[int] = Field(default_factory=list)
    select_all: bool = False
    excluded_ids: list[int] = Field(default_factory=list)
    filter_status: CallStatus | None = None
    search: str | None = None


class PhoneNumberBulkResult(BaseModel):
    updated: int = 0
    reset: int = 0
    deleted: int = 0
