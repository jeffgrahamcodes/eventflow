import json
from typing import Any

from eventflow.bus import EventBus
from eventflow.events import (
    PaymentCharged,
    PaymentFailed,
    StockInsufficient,
)
from eventflow.services.order_service import OrderService

bus = EventBus()
order_service = OrderService(bus)


def handler(event: dict[str, Any], context: Any) -> None:
    for record in event["Records"]:
        body = json.loads(record["body"])
        detail_type = body["detail-type"]
        detail = body["detail"]

        if detail_type == "payment.charged":
            event_obj = PaymentCharged.model_validate(detail)
            order_service.handle_payment_charged(event_obj)
        elif detail_type == "payment.failed":
            event_obj = PaymentFailed.model_validate(detail)
            order_service.handle_payment_failed(event_obj)
        elif detail_type == "stock.insufficient":
            event_obj = StockInsufficient.model_validate(detail)
            order_service.handle_stock_insufficient(event_obj)
