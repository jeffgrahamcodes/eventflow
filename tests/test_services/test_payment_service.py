from uuid import uuid4

from eventflow.events import (
    CancellationReason,
    OrderCancelled,
    PaymentCharged,
    PaymentFailed,
    PaymentRefunded,
    StockReserved,
)
from eventflow.services.payment_service import PaymentService
from tests.conftest import FakeEventBus


def test_charge_publishes_payment_charged_event(bus: FakeEventBus) -> None:
    _service = PaymentService(bus)

    bus.publish(
        StockReserved(
            order_id=uuid4(),
            customer_id=uuid4(),
            correlation_id=uuid4(),
            reserved_items=[{"sku": "WIDGET-OO1", "quantity": 1, "price": 24.99}],
            total_amount=24.99,
        )
    )

    assert isinstance(bus.published_events[1], PaymentCharged)
    assert bus.published_events[1].event_type == "payment.charged"


def test_failed_charge_publishes_payment_failed_event(bus: FakeEventBus) -> None:
    _service = PaymentService(bus, should_fail=True)

    bus.publish(
        StockReserved(
            order_id=uuid4(),
            customer_id=uuid4(),
            correlation_id=uuid4(),
            reserved_items=[{"sku": "WIDGET-001", "quantity": 1, "price": 24.99}],
            total_amount=49.98,
        )
    )

    assert isinstance(bus.published_events[1], PaymentFailed)
    assert bus.published_events[1].event_type == "payment.failed"


def test_refund_publishes_payment_refunded_event(bus: FakeEventBus) -> None:
    _service = PaymentService(bus)

    order_id = uuid4()
    customer_id = uuid4()
    correlation_id = uuid4()

    bus.publish(
        StockReserved(
            order_id=order_id,
            customer_id=customer_id,
            correlation_id=correlation_id,
            reserved_items=[{"sku": "WIDGET-001", "quantity": 1, "price": 24.99}],
            total_amount=49.98,
        )
    )

    bus.publish(
        OrderCancelled(
            order_id=order_id,
            customer_id=customer_id,
            correlation_id=correlation_id,
            reason=CancellationReason.CUSTOMER_REQUESTED,
            items=[{"sku": "WIDGET-001", "quantity": 1, "price": 24.99}],
        )
    )

    assert isinstance(bus.published_events[3], PaymentRefunded)
    assert bus.published_events[3].refund_amount == 49.98
