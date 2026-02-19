from datetime import datetime
from pydantic import BaseModel, Field


class BillingInfo(BaseModel):
    wallet_balance: int = Field(..., description="Current wallet balance in Toman")
    cost_per_connected: int = Field(..., description="Cost per connected call in Toman")
    currency: str = "Toman"
    disabled_by_dialer: bool = False


class BillingUpdate(BaseModel):
    wallet_balance: int | None = Field(default=None, description="New wallet balance in Toman")
    cost_per_connected: int | None = Field(default=None, description="New cost per connected call in Toman")


class WalletManualAdjustRequest(BaseModel):
    amount_toman: int = Field(..., gt=0)
    operation: str = Field(..., pattern="^(ADD|SUBTRACT)$")
    note: str | None = Field(default=None, max_length=500)


class WalletTopupMatchRequest(BaseModel):
    amount_toman: int = Field(..., gt=0)
    jalali_date: str = Field(..., pattern=r"^\d{4}/\d{2}/\d{2}$")
    hour: int = Field(..., ge=0, le=23)
    minute: int = Field(..., ge=0, le=59)


class WalletTransactionOut(BaseModel):
    id: int
    amount_toman: int
    balance_after: int
    source: str
    note: str | None = None
    transaction_at: datetime
    created_at: datetime
    created_by_user_id: int | None = None
    created_by_username: str | None = None


class WalletTransactionListOut(BaseModel):
    items: list[WalletTransactionOut]
    total: int
