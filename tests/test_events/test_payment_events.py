from uuid import uuid4

import pytest
from pydantic import ValidationError

from eventflow.events import PaymentCharged, PaymentFailed, PaymentFailureReason


# PaymentCharged tests
def test_payment_charged_valid_construction() -> None:
    event = PaymentCharged(
        order_id=uuid4(),
        customer_id=uuid4(),
        correlation_id=uuid4(),
        charge_amount=49.99,
        payment_method_last_four="1234",
    )

    assert event.event_type == "payment.charged"
    assert event.charge_amount == 49.99
    assert event.payment_method_last_four == "1234"


def test_payment_charged_rejects_zero_charge_amount() -> None:
    with pytest.raises(ValidationError):
        PaymentCharged(
            order_id=uuid4(),
            customer_id=uuid4(),
            correlation_id=uuid4(),
            charge_amount=0,
            payment_method_last_four="1234",
        )


def test_payment_charged_rejects_negative_charge_amount() -> None:
    with pytest.raises(ValidationError):
        PaymentCharged(
            order_id=uuid4(),
            customer_id=uuid4(),
            correlation_id=uuid4(),
            charge_amount=-10.00,
            payment_method_last_four="1234",
        )


def test_payment_charged_rejects_invalid_payment_method_last_four() -> None:
    with pytest.raises(ValidationError):
        PaymentCharged(
            order_id=uuid4(),
            customer_id=uuid4(),
            correlation_id=uuid4(),
            charge_amount=10.00,
            payment_method_last_four="123",
        )


def test_payment_charged_rejects_non_digit_payment_method_last_four() -> None:
    with pytest.raises(ValidationError):
        PaymentCharged(
            order_id=uuid4(),
            customer_id=uuid4(),
            correlation_id=uuid4(),
            charge_amount=10.00,
            payment_method_last_four="12ab",
        )


# Payment failed
def test_payment_failed_valid_construction() -> None:
    event = PaymentFailed(
        order_id=uuid4(),
        customer_id=uuid4(),
        correlation_id=uuid4(),
        failure_amount=49.99,
        reason=PaymentFailureReason.CARD_DECLINED,
    )

    assert event.event_type == "payment.failed"
    assert event.failure_amount == 49.99


def test_payment_failed_rejects_zero_failure_amount() -> None:
    with pytest.raises(ValidationError):
        PaymentFailed(
            order_id=uuid4(),
            customer_id=uuid4(),
            correlation_id=uuid4(),
            failure_amount=0,
            reason=PaymentFailureReason.CARD_DECLINED,
        )


def test_payment_failed_rejects_negative_failure_amount() -> None:
    with pytest.raises(ValidationError):
        PaymentFailed(
            order_id=uuid4(),
            customer_id=uuid4(),
            correlation_id=uuid4(),
            failure_amount=-10.00,
            reason=PaymentFailureReason.CARD_DECLINED,
        )
