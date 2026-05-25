import json
from typing import Any

from eventflow.bus import EventBus
from eventflow.events import OrderCancelled, PaymentCharged, StockReserved
from eventflow.services.payment_service import PaymentService

bus = EventBus()
payment_service = PaymentService(bus)


def handler(event: dict[str, Any], context: Any) -> None:
    for record in event["Records"]:
        body = json.loads(record["body"])
        detail_type = body["detail-type"]
        detail = body["detail"]

        if detail_type == "stock.reserved":
            event_obj = StockReserved.model_validate(detail)
            payment_service.charge(event_obj)
        elif detail_type == "order.cancelled":
            event_obj = OrderCancelled.model_validate(detail)
            payment_service.refund(event_obj)
        elif detail_type == "payment.charged":
            event_obj = PaymentCharged.model_validate(detail)
            payment_service.handle_payment_charged(event_obj)
