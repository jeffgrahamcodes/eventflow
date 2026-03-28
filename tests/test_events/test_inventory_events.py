from uuid import uuid4

import pytest
from pydantic import ValidationError

from eventflow.events import StockInsufficient


# StockInsufficient tests
def test_stock_insufficient_valid_construction() -> None:
    event = StockInsufficient(
        order_id=uuid4(),
        customer_id=uuid4(),
        correlation_id=uuid4(),
        insufficient_items=[{"sku": "WIDGET-001", "quantity": 2, "price": 24.99}],
        available_quantities=[{"sku": "WIDGET-002", "quantity": 2, "price": 24.99}],
    )

    assert event.event_type == "stock.insufficient"


def test_stock_insufficient_rejects_insufficient_items_list() -> None:
    with pytest.raises(ValidationError):
        StockInsufficient(  # type: ignore[call-arg]
            order_id=uuid4(),
            customer_id=uuid4(),
            correlation_id=uuid4(),
            insufficient_items=[],
        )


def test_stock_insufficient_rejects_mismatched_quantities() -> None:
    with pytest.raises(ValidationError):
        StockInsufficient(
            order_id=uuid4(),
            customer_id=uuid4(),
            correlation_id=uuid4(),
            insufficient_items=[{"sku": "WIDGET-001", "quantity": 2, "price": 24.99}],
            available_quantities=[],
        )
