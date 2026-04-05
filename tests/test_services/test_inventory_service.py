from uuid import uuid4

from eventflow.events import (
    CancellationReason,
    OrderCancelled,
    OrderValidated,
    StockInsufficient,
    StockReserved,
)
from eventflow.services.inventory_service import InventoryService
from tests.conftest import FakeEventBus


def test_reserve_stock_publishes_stock_reserved_event(bus: FakeEventBus) -> None:
    _service = InventoryService(bus)

    bus.publish(
        OrderValidated(
            order_id=uuid4(),
            customer_id=uuid4(),
            correlation_id=uuid4(),
            items=[{"sku": "WIDGET-001", "quantity": 2, "price": 24.99}],
        )
    )

    assert isinstance(bus.published_events[1], StockReserved)
    assert bus.published_events[1].event_type == "stock.reserved"


def test_reserve_stock_publishes_stock_insufficient_event_when_quantity_unavailable(
    bus: FakeEventBus,
) -> None:
    _service = InventoryService(bus)

    bus.publish(
        OrderValidated(
            order_id=uuid4(),
            customer_id=uuid4(),
            correlation_id=uuid4(),
            items=[{"sku": "WIDGET-OOS", "quantity": 1, "price": 24.99}],
        )
    )

    assert isinstance(bus.published_events[1], StockInsufficient)
    assert bus.published_events[1].event_type == "stock.insufficient"


def test_release_stock_restores_inventory(bus: FakeEventBus) -> None:
    service = InventoryService(bus)  # no underscore — need the reference

    initial_quantity = service._inventory["WIDGET-001"]

    bus.publish(
        OrderCancelled(
            order_id=uuid4(),
            customer_id=uuid4(),
            correlation_id=uuid4(),
            reason=CancellationReason.STOCK_INSUFFICIENT,
            items=[{"sku": "WIDGET-001", "quantity": 2, "price": 24.99}],
        )
    )

    assert service._inventory["WIDGET-001"] == initial_quantity + 2
