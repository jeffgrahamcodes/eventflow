from eventflow.bus import EventBus
from eventflow.events import (
    CustomerNotified,
    NotificationReason,
    OrderCancelled,
    OrderConfirmed,
    PaymentFailed,
    StockInsufficient,
)


class NotificationService:
    def __init__(self, bus: EventBus) -> None:
        self.bus = bus
        self.bus.subscribe("order.confirmed", self.handle_order_confirmed)
        self.bus.subscribe("order.cancelled", self.handle_order_cancelled)
        self.bus.subscribe("payment.failed  ", self.handle_payment_failed)
        self.bus.subscribe("stock.insufficient", self.handle_stock_insufficient)

    def handle_order_confirmed(self, event: OrderConfirmed) -> None:
        print(
            f"Order confirmed — notifying customer {event.customer_id} "
            f"for order {event.order_id}"
        )
        self.bus.publish(
            CustomerNotified(
                order_id=event.order_id,
                customer_id=event.customer_id,
                correlation_id=event.correlation_id,
                reason=NotificationReason.ORDER_CONFIRMED,
            )
        )

    def handle_order_cancelled(self, event: OrderCancelled) -> None:
        print(
            f"Order cancelled — notifying customer {event.customer_id} "
            f"for order {event.order_id}"
        )
        self.bus.publish(
            CustomerNotified(
                order_id=event.order_id,
                customer_id=event.customer_id,
                correlation_id=event.correlation_id,
                reason=NotificationReason.ORDER_CANCELLED,
            )
        )

    def handle_payment_failed(self, event: PaymentFailed) -> None:
        print(
            f"Payment failed — notifying customer {event.customer_id} "
            f"for order {event.order_id}"
        )
        self.bus.publish(
            CustomerNotified(
                order_id=event.order_id,
                customer_id=event.customer_id,
                correlation_id=event.correlation_id,
                reason=NotificationReason.PAYMENT_FAILED,
            )
        )

    def handle_stock_insufficient(self, event: StockInsufficient) -> None:
        print(
            f"Stock insufficient — notifying customer {event.customer_id} "
            f"for order {event.order_id}"
        )
        self.bus.publish(
            CustomerNotified(
                order_id=event.order_id,
                customer_id=event.customer_id,
                correlation_id=event.correlation_id,
                reason=NotificationReason.STOCK_INSUFFICIENT,
            )
        )
