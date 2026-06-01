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


def publish(event_obj: Any) -> None:
    events_client.put_events(
        Entries=[
            {
                "Source": "eventflow.notification-service",
                "DetailType": event_obj.event_type,
                "Detail": event_obj.model_dump_json(),
                "EventBusName": EVENT_BUS_NAME,
            }
        ]
    )


def handler(event: dict[str, Any], context: Any) -> None:
    for record in event["Records"]:
        body = json.loads(record["body"])
        detail_type = body["detail-type"]
        detail = body["detail"]

        if detail_type == "order.confirmed":
            confirmed = OrderConfirmed.model_validate(detail)
            print(f"Order confirmed — notifying customer {confirmed.customer_id}")
            publish(
                CustomerNotified(
                    order_id=confirmed.order_id,
                    customer_id=confirmed.customer_id,
                    correlation_id=confirmed.correlation_id,
                    reason=NotificationReason.ORDER_CONFIRMED,
                )
            )

        elif detail_type == "order.cancelled":
            cancelled = OrderCancelled.model_validate(detail)
            print(f"Order cancelled — notifying customer {cancelled.customer_id}")
            publish(
                CustomerNotified(
                    order_id=cancelled.order_id,
                    customer_id=cancelled.customer_id,
                    correlation_id=cancelled.correlation_id,
                    reason=NotificationReason.ORDER_CANCELLED,
                )
            )

        elif detail_type == "payment.failed":
            failed = PaymentFailed.model_validate(detail)
            print(f"Payment failed — notifying customer {failed.customer_id}")
            publish(
                CustomerNotified(
                    order_id=failed.order_id,
                    customer_id=failed.customer_id,
                    correlation_id=failed.correlation_id,
                    reason=NotificationReason.PAYMENT_FAILED,
                )
            )

        elif detail_type == "stock.insufficient":
            insufficient = StockInsufficient.model_validate(detail)
            print(f"Stock insufficient — notifying customer {insufficient.customer_id}")
            publish(
                CustomerNotified(
                    order_id=insufficient.order_id,
                    customer_id=insufficient.customer_id,
                    correlation_id=insufficient.correlation_id,
                    reason=NotificationReason.STOCK_INSUFFICIENT,
                )
            )
