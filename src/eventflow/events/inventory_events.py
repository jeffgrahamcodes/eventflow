from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ValidationInfo, field_validator


class StockReserved(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str = "stock.reserved"
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    correlation_id: UUID

    # Domain payload
    order_id: UUID
    customer_id: UUID
    reserved_items: list[dict]
    reserved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class StockInsufficient(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str = "stock.insufficient"
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    correlation_id: UUID

    # Domain payload
    order_id: UUID
    customer_id: UUID
    insufficient_items: list[dict]
    available_quantities: list[dict]
    insufficient_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("insufficient_items")
    @classmethod
    def insufficient_items_must_not_be_empty(cls, v: list[dict]) -> list[dict]:
        if not v:
            raise ValueError("insufficient_items must not be empty")
        return v

    @field_validator("available_quantities")
    @classmethod
    def available_quantities_must_match_insufficient_items(
        cls, v: list[dict], info: ValidationInfo
    ) -> list[dict]:
        insufficient = info.data.get("insufficient_items", [])
        if len(v) != len(insufficient):
            raise ValueError(
                f"available_quantities length {len(v)} must match "
                f"insufficient_items length {len(insufficient)}"
            )
        return v
