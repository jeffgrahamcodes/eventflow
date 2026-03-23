from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class PaymentFailureReason(StrEnum):
    INSUFFICIENT_FUNDS = "insufficient_funds"
    CARD_DECLINED = "card_declined"
    CARD_EXPIRED = "card_expired"
    INVALID_CARD = "invalid_card"
    PROCESSOR_ERROR = "processor_error"


class PaymentCharged(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str = "payment.charged"
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    correlation_id: UUID

    # Domain payload
    order_id: UUID
    customer_id: UUID
    charge_amount: float
    payment_method_last_four: str
    charged_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PaymentFailed(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str = "payment.failed"
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    correlation_id: UUID

    # Domain payload
    order_id: UUID
    customer_id: UUID
    failure_amount: float
    reason: PaymentFailureReason
    failed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
