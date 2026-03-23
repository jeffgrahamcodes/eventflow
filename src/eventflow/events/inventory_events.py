from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


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
