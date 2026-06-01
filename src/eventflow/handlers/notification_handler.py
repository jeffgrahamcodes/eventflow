import json
import os
from typing import Any

import boto3

from eventflow.events import (
    CustomerNotified,
    NotificationReason,
    OrderCancelled,
    OrderConfirmed,
    PaymentFailed,
    StockInsufficient,
)

events_client = boto3.client("events")
EVENT_BUS_NAME = os.environ.get("EVENT_BUS_NAME", "eventflow-dev-bus")


def publish(event_obj) -> None:
    events_client.put_events(Entries=[{
        "Source": "eventflow.notification-service",
        "DetailType": event_obj.event_type,
        "Detail": event_obj.model_dump_json(),
        "EventBusName": EVENT_BUS_NAME,
    }])


def handler(event: dict[str, Any], context: Any) -> None:
    for record in event["Records"]:
        body = json.loads(record["body"])
        detail_type = body["detail-type"]
        detail = body["detail"]

        if detail_type == "order.confirmed":
            event_obj = OrderConfirmed.model_validate(detail)
            print(f"Order confirmed — notifying customer {event_obj.customer_id}")
            publish(CustomerNotified(
                order_id=event_obj.order_id,
                customer_id=event_obj.customer_id,
                correlation_id=event_obj.correlation_id,
                reason=NotificationReason.ORDER_CONFIRMED,
            ))

        elif detail_type == "order.cancelled":
            event_obj = OrderCancelled.model_validate(detail)
            print(f"Order cancelled — notifying customer {event_obj.customer_id}")
            publish(CustomerNotified(
                order_id=event_obj.order_id,
                customer_id=event_obj.customer_id,
                correlation_id=event_obj.correlation_id,
                reason=NotificationReason.ORDER_CANCELLED,
            ))

        elif detail_type == "payment.failed":
            event_obj = PaymentFailed.model_validate(detail)
            print(f"Payment failed — notifying customer {event_obj.customer_id}")
            publish(CustomerNotified(
                order_id=event_obj.order_id,
                customer_id=event_obj.customer_id,
                correlation_id=event_obj.correlation_id,
                reason=NotificationReason.PAYMENT_FAILED,
            ))

        elif detail_type == "stock.insufficient":
            event_obj = StockInsufficient.model_validate(detail)
            print(f"Stock insufficient — notifying customer {event_obj.customer_id}")
            publish(CustomerNotified(
                order_id=event_obj.order_id,
                customer_id=event_obj.customer_id,
                correlation_id=event_obj.correlation_id,
                reason=NotificationReason.STOCK_INSUFFICIENT,
            ))