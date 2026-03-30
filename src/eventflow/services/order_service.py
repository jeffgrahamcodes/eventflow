from uuid import UUID

from eventflow.bus import EventBus
from eventflow.events import (
    CancellationReason,
    OrderCancelled,
    OrderPlaced,
    OrderValidated,
    PaymentCharged,
    PaymentFailed,
    StockInsufficient,
)


class OrderService:
    def __init__(self, bus: EventBus) -> None:
        self.bus = bus
        self.bus.subscribe("order.placed", self.validate_order)
        self.bus.subscribe("payment.charged", self.handle_payment_charged)
        self.bus.subscribe("payment.failed", self.handle_payment_failed)
        self.bus.subscribe("stock.insufficient", self.handle_stock_insufficient)

    def place_order(
        self,
        order_id: UUID,
        customer_id: UUID,
        items: list[dict],
        total_amount: float,
        shipping_address: str,
    ) -> OrderPlaced:
        event = OrderPlaced(
            order_id=order_id,
            customer_id=customer_id,
            items=items,
            total_amount=total_amount,
            shipping_address=shipping_address,
        )

        self.bus.publish(event)
        return event

    def validate_order(self, event: OrderPlaced) -> None:
        if not event.items or event.total_amount <= 0:
            cancelled = OrderCancelled(
                order_id=event.order_id,
                customer_id=event.customer_id,
                correlation_id=event.correlation_id,
                reason=CancellationReason.CUSTOMER_REQUESTED,
            )
            self.bus.publish(cancelled)
            return

        validated = OrderValidated(
            order_id=event.order_id,
            customer_id=event.customer_id,
            correlation_id=event.correlation_id,
        )

        self.bus.publish(validated)

    def handle_payment_charged(self, event: PaymentCharged) -> None:
        pass

    def handle_payment_failed(self, event: PaymentFailed) -> None:
        pass

    def handle_stock_insufficient(self, event: StockInsufficient) -> None:
        pass
