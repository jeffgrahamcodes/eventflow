from uuid import UUID

from eventflow.bus import EventBus
from eventflow.events import (
    OrderCancelled,
    PaymentCharged,
    PaymentFailed,
    PaymentFailureReason,
    PaymentRefunded,
    StockReserved,
)


class PaymentService:
    def __init__(self, bus: EventBus, should_fail: bool = False) -> None:
        self.bus = bus
        self.bus.subscribe("stock.reserved", self.charge)
        self.bus.subscribe("payment.charged", self.handle_payment_charged)
        self.bus.subscribe("order.cancelled", self.refund)
        self.should_fail = should_fail
        self._pending_charges: dict[UUID, float] = {}

    def charge(self, event: StockReserved) -> None:
        if self.should_fail:
            self.bus.publish(
                PaymentFailed(
                    order_id=event.order_id,
                    customer_id=event.customer_id,
                    correlation_id=event.correlation_id,
                    failure_amount=event.total_amount,
                    reason=PaymentFailureReason.CARD_DECLINED,
                )
            )
            return

        self.bus.publish(
            PaymentCharged(
                order_id=event.order_id,
                customer_id=event.customer_id,
                correlation_id=event.correlation_id,
                charge_amount=event.total_amount,
                payment_method_last_four="1234",
            )
        )

    def refund(self, event: OrderCancelled) -> None:
        refund_amount = self._pending_charges.pop(event.order_id, None)
        if refund_amount is None:
            return
        self.bus.publish(
            PaymentRefunded(
                order_id=event.order_id,
                customer_id=event.customer_id,
                correlation_id=event.correlation_id,
                refund_amount=refund_amount,
            )
        )

    def handle_payment_charged(self, event: PaymentCharged) -> None:
        self._pending_charges[event.order_id] = event.charge_amount
