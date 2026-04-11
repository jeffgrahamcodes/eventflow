from uuid import uuid4

from eventflow.bus import EventBus
from eventflow.events import (
    CustomerNotified,
    NotificationReason,
)
from eventflow.services.inventory_service import InventoryService
from eventflow.services.notification_service import NotificationService
from eventflow.services.order_service import OrderService
from eventflow.services.payment_service import PaymentService


def test_happy_path_order_placed_to_customer_notified() -> None:
    bus = EventBus()
    collected_events: list = []

    for event_type in [
        "order.placed",
        "order.validated",
        "order.confirmed",
        "order.cancelled",
        "stock.reserved",
        "stock.insufficient",
        "payment.charged",
        "payment.failed",
        "payment.refunded",
        "customer.notified",
    ]:
        bus.subscribe(event_type, collected_events.append)

    order_service = OrderService(bus)
    InventoryService(bus)
    PaymentService(bus)
    NotificationService(bus)

    order_service.place_order(
        order_id=uuid4(),
        customer_id=uuid4(),
        items=[{"sku": "WIDGET-001", "quantity": 2, "price": 24.99}],
        total_amount=49.98,
        shipping_address="123 Main St, Philadelphia, PA 19103",
    )

    event_types = [e.event_type for e in collected_events]

    assert event_types[0] == "order.placed"
    assert event_types[1] == "order.validated"
    assert event_types[2] == "stock.reserved"
    assert event_types[3] == "payment.charged"
    assert event_types[4] == "order.confirmed"
    assert event_types[5] == "customer.notified"

    assert isinstance(collected_events[5], CustomerNotified)
    assert collected_events[5].reason == NotificationReason.ORDER_CONFIRMED
