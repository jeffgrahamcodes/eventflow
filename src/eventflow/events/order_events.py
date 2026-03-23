from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class CancellationReason(StrEnum):
    PAYMENT_FAILED = "payment_failed"
    STOCK_INSUFFICIENT = "stock_insufficient"
    CUSTOMER_REQUESTED = "customer_requested"


class OrderPlaced(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str = "order.placed"
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    correlation_id: UUID = Field(default_factory=uuid4)

    # Domain payload
    order_id: UUID
    customer_id: UUID
    items: list[dict]
    total_amount: float
    shipping_address: str


class OrderValidated(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str = "order.validated"
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    correlation_id: UUID

    # Domain payload
    order_id: UUID
    customer_id: UUID
    validated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class OrderConfirmed(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str = "order.confirmed"
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    correlation_id: UUID

    # Domain payload
    order_id: UUID
    customer_id: UUID
    confirmed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class OrderCancelled(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str = "order.cancelled"
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    correlation_id: UUID

    # Domain payload
    order_id: UUID
    customer_id: UUID
    reason: CancellationReason
    cancelled_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
