import json
import os
from decimal import Decimal
from typing import Any

import boto3

from eventflow.events import OrderValidated, PaymentCharged, PaymentFailed, StockInsufficient

dynamodb = boto3.resource("dynamodb")
orders_table = dynamodb.Table(os.environ["ORDERS_TABLE_NAME"])
events_client = boto3.client("events")
EVENT_BUS_NAME = os.environ.get("EVENT_BUS_NAME", "eventflow-dev-bus")


def publish(event_obj) -> None:
    events_client.put_events(Entries=[{
        "Source": "eventflow.order-service",
        "DetailType": event_obj.event_type,
        "Detail": event_obj.model_dump_json(),
        "EventBusName": EVENT_BUS_NAME,
    }])


def handler(event: dict[str, Any], context: Any) -> None:
    for record in event["Records"]:
        body = json.loads(record["body"])
        detail_type = body["detail-type"]
        detail = body["detail"]

        if detail_type == "order.placed":
            orders_table.put_item(Item={
                "order_id": detail["order_id"],
                "customer_id": detail["customer_id"],
                "status": "placed",
                "total_amount": Decimal(str(detail["total_amount"])),
                "items": json.dumps(detail["items"]),
            })
            validated = OrderValidated(
                order_id=detail["order_id"],
                customer_id=detail["customer_id"],
                correlation_id=detail["correlation_id"],
                items=detail["items"],
                total_amount=detail["total_amount"],
            )
            publish(validated)

        elif detail_type == "payment.charged":
            event_obj = PaymentCharged.model_validate(detail)
            orders_table.update_item(
                Key={"order_id": detail["order_id"]},
                UpdateExpression="SET #s = :s",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues={":s": "confirmed"},
            )

        elif detail_type == "payment.failed":
            event_obj = PaymentFailed.model_validate(detail)
            orders_table.update_item(
                Key={"order_id": detail["order_id"]},
                UpdateExpression="SET #s = :s",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues={":s": "cancelled"},
            )

        elif detail_type == "stock.insufficient":
            event_obj = StockInsufficient.model_validate(detail)
            orders_table.update_item(
                Key={"order_id": detail["order_id"]},
                UpdateExpression="SET #s = :s",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues={":s": "cancelled"},
            )