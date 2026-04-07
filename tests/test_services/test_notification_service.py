from uuid import uuid4

from eventflow.events import (
    CancellationReason,
    NotificationReason,
    OrderCancelled,
    OrderConfirmed,
    PaymentFailed,
    PaymentFailureReason,
    StockInsufficient,
)
from eventflow.services.notification_service import (
    NotificationService,
)
from tests.conftest import FakeEventBus


def test_handle_order_confirmed(bus: FakeEventBus) -> None:
    _service = NotificationService(bus)
    bus.publish(
        OrderConfirmed(
            correlation_id=uuid4(),
            order_id=uuid4(),
            customer_id=uuid4(),
        )
    )

    assert bus.published_events[1].reason == NotificationReason.ORDER_CONFIRMED


def test_handle_order_cancelled(bus: FakeEventBus) -> None:
    _service = NotificationService(bus)
    bus.publish(
        OrderCancelled(
            correlation_id=uuid4(),
            order_id=uuid4(),
            customer_id=uuid4(),
            reason=CancellationReason.CUSTOMER_REQUESTED,
            items=[{"sku": "WIDGET-001", "quantity": 2, "price": 24.99}],
        )
    )

    assert bus.published_events[1].reason == NotificationReason.ORDER_CANCELLED


def test_handle_payment_failed(bus: FakeEventBus) -> None:
    _service = NotificationService(bus)
    bus.publish(
        PaymentFailed(
            correlation_id=uuid4(),
            order_id=uuid4(),
            customer_id=uuid4(),
            failure_amount=49.98,
            reason=PaymentFailureReason.INSUFFICIENT_FUNDS,
        )
    )

    assert bus.published_events[1].reason == NotificationReason.PAYMENT_FAILED


def test_handle_stock_insufficient(bus: FakeEventBus) -> None:
    _service = NotificationService(bus)
    bus.publish(
        StockInsufficient(
            correlation_id=uuid4(),
            order_id=uuid4(),
            customer_id=uuid4(),
            insufficient_items=[{"sku": "WIDGET-001", "quantity": 2}],
            available_quantities=[{"sku": "WIDGET-001", "available": 0}],
        )
    )

    assert bus.published_events[1].reason == NotificationReason.STOCK_INSUFFICIENT
