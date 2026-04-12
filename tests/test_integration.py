from uuid import uuid4

from eventflow.bus import EventBus
from eventflow.events import (
    CancellationReason,
    CustomerNotified,
    NotificationReason,
    OrderCancelled,
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


def test_failure_path_payment_failed_cancels_order() -> None:
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
    PaymentService(bus, should_fail=True)
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
    assert event_types[3] == "payment.failed"
    assert event_types[4] == "order.cancelled"
    assert event_types[5] == "customer.notified"
    assert event_types[6] == "customer.notified"


def test_failure_path_stock_insufficient_cancels_order() -> None:
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
        items=[{"sku": "WIDGET-OOS", "quantity": 2, "price": 24.99}],
        total_amount=49.98,
        shipping_address="123 Main St, Philadelphia, PA 19103",
    )

    event_types = [e.event_type for e in collected_events]

    assert event_types[0] == "order.placed"
    assert event_types[1] == "order.validated"
    assert event_types[2] == "stock.insufficient"
    assert event_types[3] == "order.cancelled"
    assert event_types[4] == "customer.notified"
    assert event_types[5] == "customer.notified"


def test_failure_path_payment_charged_then_order_cancelled_produces_refund() -> None:
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

    placed = order_service.place_order(
        order_id=uuid4(),
        customer_id=uuid4(),
        items=[{"sku": "WIDGET-001", "quantity": 2, "price": 24.99}],
        total_amount=49.98,
        shipping_address="123 Main St, Philadelphia, PA 19103",
    )

    event_types = [e.event_type for e in collected_events]
    assert "payment.charged" in event_types

    bus.publish(
        OrderCancelled(
            order_id=placed.order_id,
            customer_id=placed.customer_id,
            correlation_id=placed.correlation_id,
            reason=CancellationReason.CUSTOMER_REQUESTED,
            items=[{"sku": "WIDGET-001", "quantity": 2, "price": 24.99}],
        )
    )

    event_types = [e.event_type for e in collected_events]
    assert "payment.refunded" in event_types

    refund_event = next(
        e for e in collected_events if e.event_type == "payment.refunded"
    )
    assert refund_event.refund_amount == 49.98
