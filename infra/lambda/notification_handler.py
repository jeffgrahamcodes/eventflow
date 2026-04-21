import json
from typing import Any

from eventflow.bus import EventBus
from eventflow.events import (
    OrderCancelled,
    OrderConfirmed,
    PaymentFailed,
    StockInsufficient,
)
from eventflow.services.notification_service import NotificationService

bus = EventBus()
notification_service = NotificationService(bus)


def handler(event: dict[str, Any], context: Any) -> None:
    for record in event["Records"]:
        body = json.loads(record["body"])
        detail_type = body["detail-type"]
        detail = body["detail"]

        if detail_type == "order.confirmed":
            event_obj = OrderConfirmed.model_validate(detail)
            notification_service.handle_order_confirmed(event_obj)
        elif detail_type == "order.cancelled":
            event_obj = OrderCancelled.model_validate(detail)
            notification_service.handle_order_cancelled(event_obj)
        elif detail_type == "payment.failed":
            event_obj = PaymentFailed.model_validate(detail)
            notification_service.handle_payment_failed(event_obj)
        elif detail_type == "stock.insufficient":
            event_obj = StockInsufficient.model_validate(detail)
            notification_service.handle_stock_insufficient(event_obj)
