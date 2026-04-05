from uuid import UUID

from eventflow.bus import EventBus
from eventflow.events import (
    CancellationReason,
    OrderCancelled,
    OrderConfirmed,
    OrderPlaced,
    OrderValidated,
    PaymentCharged,
    PaymentFailed,
    StockInsufficient,
)


class OrderService:
    def __init__(self, bus: EventBus) -> None:
        self.bus = bus
        self._pending_items: dict[UUID, list[dict]] = {}
        self.bus.subscribe("order.placed", self.validate_order)
        self.bus.subscribe("order.validated", self.handle_order_validated)
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
        if any(item["quantity"] > 100 for item in event.items):
            cancelled = OrderCancelled(
                order_id=event.order_id,
                customer_id=event.customer_id,
                correlation_id=event.correlation_id,
                reason=CancellationReason.CUSTOMER_REQUESTED,
                items=event.items,
            )
            self.bus.publish(cancelled)
            return

        validated = OrderValidated(
            order_id=event.order_id,
            customer_id=event.customer_id,
            correlation_id=event.correlation_id,
            items=event.items,
            total_amount=event.total_amount,
        )
        self.bus.publish(validated)

    def handle_payment_charged(self, event: PaymentCharged) -> None:
        self._pending_items.pop(event.order_id, [])
        confirmed = OrderConfirmed(
            order_id=event.order_id,
            customer_id=event.customer_id,
            correlation_id=event.correlation_id,
        )
        self.bus.publish(confirmed)

    def handle_payment_failed(self, event: PaymentFailed) -> None:
        items = self._pending_items.pop(event.order_id, [])
        cancelled = OrderCancelled(
            order_id=event.order_id,
            customer_id=event.customer_id,
            correlation_id=event.correlation_id,
            reason=CancellationReason.PAYMENT_FAILED,
            items=items,
        )
        self.bus.publish(cancelled)

    def handle_stock_insufficient(self, event: StockInsufficient) -> None:
        items = self._pending_items.pop(event.order_id, [])
        cancelled = OrderCancelled(
            order_id=event.order_id,
            customer_id=event.customer_id,
            correlation_id=event.correlation_id,
            reason=CancellationReason.STOCK_INSUFFICIENT,
            items=items,
        )
        self.bus.publish(cancelled)

    def handle_order_validated(self, event: OrderValidated) -> None:
        self._pending_items[event.order_id] = event.items
