from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


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

    @field_validator("charge_amount")
    @classmethod
    def charge_amount_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError(f"charge_amount must be positive, got {v}")
        return v

    @field_validator("payment_method_last_four")
    @classmethod
    def must_be_four_digits(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 4:
            raise ValueError(f"payment_method_last_four must be four digits, got {v}")
        return v


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
