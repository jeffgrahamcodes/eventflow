from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class OrderPlaced(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    event_type: str = "order.placed"
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: UUID = Field(default_factory=uuid4)

    # Domain payload
    order_id: UUID
    customer_id: UUID
    items: list[dict]
    total_amount: float
    shipping_address: str
