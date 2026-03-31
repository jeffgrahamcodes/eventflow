from uuid import uuid4

from eventflow.events import (
    CancellationReason,
    OrderCancelled,
    OrderConfirmed,
    OrderPlaced,
    OrderValidated,
    PaymentCharged,
    PaymentFailed,
    PaymentFailureReason,
    StockInsufficient,
)
from eventflow.services.order_service import OrderService
from tests.conftest import FakeEventBus


def test_order_placed_publishes_order_placed_event(bus: FakeEventBus) -> None:
    service = OrderService(bus)

    service.place_order(
        order_id=uuid4(),
        customer_id=uuid4(),
        items=[{"sku": "WIDGET-001", "quantity": 2, "price": 24.99}],
        total_amount=49.98,
        shipping_address="123 Main St, Philadelphia, PA 19103",
    )

    assert len(bus.published_events) >= 1
    assert isinstance(bus.published_events[0], OrderPlaced)
    assert bus.published_events[0].event_type == "order.placed"


def test_validated_order_publishes_validated_order_event(bus: FakeEventBus) -> None:
    service = OrderService(bus)

    service.place_order(
        order_id=uuid4(),
        customer_id=uuid4(),
        items=[{"sku": "WIDGET-001", "quantity": 2, "price": 24.99}],
        total_amount=49.98,
        shipping_address="123 Main St, Philadelphia, PA 19103",
    )

    assert isinstance(bus.published_events[1], OrderValidated)
    assert bus.published_events[1].event_type == "order.validated"


def test_validate_order_cancels_when_quantity_exceeds_limit(
    bus: FakeEventBus,
) -> None:
    service = OrderService(bus)

    service.place_order(
        order_id=uuid4(),
        customer_id=uuid4(),
        items=[{"sku": "WIDGET-001", "quantity": 101, "price": 24.99}],
        total_amount=49.98,
        shipping_address="123 Main St, Philadelphia, PA 19103",
    )

    assert isinstance(bus.published_events[1], OrderCancelled)
    assert bus.published_events[1].event_type == "order.cancelled"


def test_handle_payment_charged(bus: FakeEventBus) -> None:
    service = OrderService(bus)
    bus.publish(
        PaymentCharged(
            order_id=uuid4(),
            customer_id=uuid4(),
            correlation_id=uuid4(),
            charge_amount=49.98,
            payment_method_last_four="1234",
        )
    )

    assert isinstance(bus.published_events[1], OrderConfirmed)
    assert bus.published_events[1].event_type == "order.confirmed"


def test_handle_payment_failed(bus: FakeEventBus) -> None:
    service = OrderService(bus)
    bus.publish(
        PaymentFailed(
            order_id=uuid4(),
            customer_id=uuid4(),
            correlation_id=uuid4(),
            failure_amount=49.98,
            reason=PaymentFailureReason.CARD_DECLINED,
        )
    )

    assert isinstance(bus.published_events[1], OrderCancelled)
    assert bus.published_events[1].reason == CancellationReason.PAYMENT_FAILED
    assert bus.published_events[1].event_type == "order.cancelled"


def test_handle_stock_insufficient(bus: FakeEventBus) -> None:
    service = OrderService(bus)

    bus.publish(
        StockInsufficient(
            order_id=uuid4(),
            customer_id=uuid4(),
            correlation_id=uuid4(),
            insufficient_items=[{"sku": "WIDGET-001", "quantity": 2}],
            available_quantities=[{"sku": "WIDGET-001", "available": 0}],
        )
    )

    assert isinstance(bus.published_events[1], OrderCancelled)
    assert bus.published_events[1].reason == CancellationReason.STOCK_INSUFFICIENT
    assert bus.published_events[1].event_type == "order.cancelled"
