from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey, Boolean, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.db import Base


class BankIncomingSms(Base):
    __tablename__ = "bank_incoming_sms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sender: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    receiver: Mapped[str | None] = mapped_column(String(32), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_bank_sender: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    parsed_amount_rial: Mapped[int | None] = mapped_column(Integer, nullable=True)
    parsed_amount_toman: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    parsed_transaction_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    parsed_is_credit: Mapped[bool | None] = mapped_column(Boolean, nullable=True, index=True)
    parse_error: Mapped[str | None] = mapped_column(String(255), nullable=True)
    consumed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True, nullable=False)
    amount_toman: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)  # MANUAL_ADJUST | BANK_MATCH
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    transaction_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("admin_users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    bank_sms_id: Mapped[int | None] = mapped_column(
        ForeignKey("bank_incoming_sms.id"),
        unique=True,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    company = relationship("Company")
    created_by = relationship("AdminUser")
    bank_sms = relationship("BankIncomingSms")
