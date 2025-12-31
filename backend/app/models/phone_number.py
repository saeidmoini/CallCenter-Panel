from datetime import datetime
from enum import Enum
from sqlalchemy import String, Integer, DateTime, Enum as PgEnum, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.db import Base


class CallStatus(str, Enum):
    IN_QUEUE = "IN_QUEUE"
    MISSED = "MISSED"
    CONNECTED = "CONNECTED"
    FAILED = "FAILED"
    NOT_INTERESTED = "NOT_INTERESTED"
    HANGUP = "HANGUP"
    DISCONNECTED = "DISCONNECTED"
    BUSY = "BUSY"
    POWER_OFF = "POWER_OFF"
    BANNED = "BANNED"
    UNKNOWN = "UNKNOWN"


class PhoneNumber(Base):
    __tablename__ = "phone_numbers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    phone_number: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    status: Mapped[CallStatus] = mapped_column(PgEnum(CallStatus), default=CallStatus.IN_QUEUE, nullable=False)
    total_attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_status_change_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    assigned_batch_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_user_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    assigned_agent_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("admin_users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    assigned_agent = relationship("AdminUser")
