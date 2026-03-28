from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class NotificationReason(StrEnum):
    ORDER_CONFIRMED = "order_confirmed"
    ORDER_CANCELLED = "order_cancelled"
    PAYMENT_FAILED = "payment_failed"
    STOCK_INSUFFICIENT = "stock_insufficient"


class CustomerNotified(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str = "customer.notified"
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    correlation_id: UUID

    # Domain payload
    order_id: UUID
    customer_id: UUID
    reason: NotificationReason
    notified_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
