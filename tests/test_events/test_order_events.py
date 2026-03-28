from datetime import datetime
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from eventflow.events import (
    CancellationReason,
    OrderCancelled,
    OrderConfirmed,
    OrderPlaced,
    OrderValidated,
)


# OrderPlaced tests
def test_order_placed_valid_construction() -> None:
    event = OrderPlaced(
        order_id=uuid4(),
        customer_id=uuid4(),
        items=[{"sku": "WIDGET-001", "quantity": 2, "price": 24.99}],
        total_amount=49.98,
        shipping_address="123 Main St, Philadelphia, PA 19103",
    )

    assert event.event_type == "order.placed"
    assert event.version == "1.0.0"
    assert event.event_id is not None
    assert event.correlation_id is not None
    assert event.timestamp is not None
    assert isinstance(event.event_id, UUID)


def test_order_placed_rejects_zero_total_amount() -> None:
    with pytest.raises(ValidationError):
        OrderPlaced(
            order_id=uuid4(),
            customer_id=uuid4(),
            items=[{"sku": "WIDGET-001", "quantity": 2, "price": 24.99}],
            total_amount=0,
            shipping_address="123 Main St, Philadelphia, PA 19103",
        )


def test_order_placed_rejects_negative_total_amount() -> None:
    with pytest.raises(ValidationError):
        OrderPlaced(
            order_id=uuid4(),
            customer_id=uuid4(),
            items=[{"sku": "WIDGET-001", "quantity": 2, "price": 24.99}],
            total_amount=-10.00,
            shipping_address="123 Main St, Philadelphia, PA 19103",
        )


def test_order_placed_rejects_empty_items_list() -> None:
    with pytest.raises(ValidationError):
        OrderPlaced(
            order_id=uuid4(),
            customer_id=uuid4(),
            items=[],
            total_amount=10.00,
            shipping_address="123 Main St, Philadelphia, PA 19103",
        )


def test_order_placed_auto_generates_ids() -> None:
    event1 = OrderPlaced(
        order_id=uuid4(),
        customer_id=uuid4(),
        items=[{"sku": "WIDGET-001", "quantity": 2, "price": 24.99}],
        total_amount=10.00,
        shipping_address="123 Main St, Philadelphia, PA 19103",
    )

    event2 = OrderPlaced(
        order_id=uuid4(),
        customer_id=uuid4(),
        items=[{"sku": "WIDGET-002", "quantity": 3, "price": 124.99}],
        total_amount=10.00,
        shipping_address="123 Main St, Philadelphia, PA 19103",
    )

    assert event1.event_id != event2.event_id
    assert event1.correlation_id != event2.correlation_id
    assert isinstance(event1.event_id, UUID)
    assert isinstance(event1.timestamp, datetime)


def test_order_placed_round_trip_serialization() -> None:
    event = OrderPlaced(
        order_id=uuid4(),
        customer_id=uuid4(),
        items=[{"sku": "WIDGET-001", "quantity": 2, "price": 24.99}],
        total_amount=49.98,
        shipping_address="123 Main St, Philadelphia, PA 19103",
    )

    json_str = event.model_dump_json()
    reconstructed = OrderPlaced.model_validate_json(json_str)

    assert reconstructed.order_id == event.order_id
    assert reconstructed.event_type == event.event_type
    assert reconstructed.correlation_id == event.correlation_id
    assert reconstructed.total_amount == event.total_amount
    assert reconstructed.items == event.items


# OrderValidated tests
def test_order_validated_valid_construction() -> None:
    event = OrderValidated(
        order_id=uuid4(),
        customer_id=uuid4(),
        correlation_id=uuid4(),
    )

    assert event.event_type == "order.validated"


def test_order_validated_requires_correlation_id() -> None:
    with pytest.raises(ValidationError):
        OrderValidated(  # type: ignore[call-arg]
            order_id=uuid4(),
            customer_id=uuid4(),
        )


def test_order_validated_round_trip_serialization() -> None:
    event = OrderValidated(
        order_id=uuid4(),
        customer_id=uuid4(),
        correlation_id=uuid4(),
    )

    json_str = event.model_dump_json()
    reconstructed = OrderValidated.model_validate_json(json_str)

    assert reconstructed.order_id == event.order_id
    assert reconstructed.customer_id == event.customer_id
    assert reconstructed.correlation_id == event.correlation_id


# OrderConfirmed tests
def test_order_confirmed_valid_construction() -> None:
    event = OrderConfirmed(
        order_id=uuid4(),
        customer_id=uuid4(),
        correlation_id=uuid4(),
    )

    assert event.event_type == "order.confirmed"


def test_order_confirmed_requires_correlation_id() -> None:
    with pytest.raises(ValidationError):
        OrderConfirmed(  # type: ignore[call-arg]
            order_id=uuid4(),
            customer_id=uuid4(),
        )


def test_order_confirmed_round_trip_serialization() -> None:
    event = OrderConfirmed(
        order_id=uuid4(),
        customer_id=uuid4(),
        correlation_id=uuid4(),
    )

    json_str = event.model_dump_json()
    reconstructed = OrderConfirmed.model_validate_json(json_str)

    assert reconstructed.order_id == event.order_id
    assert reconstructed.customer_id == event.customer_id
    assert reconstructed.correlation_id == event.correlation_id


# OrderCancelled tests
def test_order_cancelled_valid_construction() -> None:
    event = OrderCancelled(
        order_id=uuid4(),
        customer_id=uuid4(),
        correlation_id=uuid4(),
        reason=CancellationReason.PAYMENT_FAILED,
    )

    assert event.event_type == "order.cancelled"
    assert event.version == "1.0.0"
    assert event.reason == CancellationReason.PAYMENT_FAILED
    assert isinstance(event.event_id, UUID)
    assert isinstance(event.cancelled_at, datetime)


def test_order_cancelled_rejects_invalid_reason() -> None:
    with pytest.raises(ValidationError):
        OrderCancelled(  # type: ignore[arg-type]
            order_id=uuid4(),
            customer_id=uuid4(),
            correlation_id=uuid4(),
            reason="invalid reason",  # type: ignore[arg-type]
        )


def test_order_cancelled_all_valid_reasons() -> None:
    for reason in CancellationReason:
        event = OrderCancelled(
            order_id=uuid4(),
            customer_id=uuid4(),
            correlation_id=uuid4(),
            reason=reason,
        )

        assert event.reason == reason


def test_order_cancelled_requires_correlation_id() -> None:
    with pytest.raises(ValidationError):
        OrderCancelled(  # type: ignore[call-arg]
            order_id=uuid4(),
            customer_id=uuid4(),
            reason=CancellationReason.PAYMENT_FAILED,
        )


def test_order_cancelled_round_trip_serialization() -> None:
    event = OrderCancelled(
        order_id=uuid4(),
        customer_id=uuid4(),
        correlation_id=uuid4(),
        reason=CancellationReason.STOCK_INSUFFICIENT,
    )

    json_str = event.model_dump_json()
    reconstructed = OrderCancelled.model_validate_json(json_str)

    assert reconstructed.order_id == event.order_id
    assert reconstructed.customer_id == event.customer_id
    assert reconstructed.reason == event.reason
    assert reconstructed.correlation_id == event.correlation_id
