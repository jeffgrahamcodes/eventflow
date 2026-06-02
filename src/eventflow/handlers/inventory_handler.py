import json
import os
from typing import Any

import boto3

from eventflow.events import (
    OrderCancelled,
    OrderValidated,
    StockInsufficient,
    StockReserved,
)

dynamodb = boto3.resource("dynamodb")
inventory_table = dynamodb.Table(os.environ["INVENTORY_TABLE_NAME"])
events_client = boto3.client("events")
EVENT_BUS_NAME = os.environ.get("EVENT_BUS_NAME", "eventflow-dev-bus")

# In-memory inventory — replaced by DynamoDB in production
_inventory: dict[str, int] = {
    "WIDGET-001": 50,
    "WIDGET-002": 12,
    "WIDGET-003": 25,
    "WIDGET-OOS": 0,
}


def publish(event_obj: Any) -> None:
    events_client.put_events(
        Entries=[
            {
                "Source": "eventflow.inventory-service",
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

        if detail_type == "order.validated":
            validated = OrderValidated.model_validate(detail)
            items = validated.items
            insufficient_items = []
            available_quantities = []

            for item in items:
                sku = item["sku"]
                quantity = item["quantity"]
                available = _inventory.get(sku, 0)
                if available < quantity:
                    insufficient_items.append({"sku": sku, "quantity": quantity})
                    available_quantities.append({"sku": sku, "available": available})

            if insufficient_items:
                publish(
                    StockInsufficient(
                        order_id=validated.order_id,
                        customer_id=validated.customer_id,
                        correlation_id=validated.correlation_id,
                        insufficient_items=insufficient_items,
                        available_quantities=available_quantities,
                    )
                )
                return

            reserved_items = []
            for item in items:
                sku = item["sku"]
                quantity = item["quantity"]
                _inventory[sku] -= quantity
                reserved_items.append({"sku": sku, "quantity": quantity})

                # Write inventory record to DynamoDB
                inventory_table.put_item(
                    Item={
                        "sku_id": sku,
                        "available_quantity": _inventory[sku],
                        "reserved_quantity": quantity,
                        "order_id": str(validated.order_id),
                    }
                )

            publish(
                StockReserved(
                    order_id=validated.order_id,
                    customer_id=validated.customer_id,
                    correlation_id=validated.correlation_id,
                    reserved_items=reserved_items,
                    total_amount=validated.total_amount,
                )
            )

        elif detail_type == "order.cancelled":
            cancelled = OrderCancelled.model_validate(detail)
            for item in cancelled.items:
                sku = item["sku"]
                quantity = item["quantity"]
                _inventory[sku] = _inventory.get(sku, 0) + quantity
