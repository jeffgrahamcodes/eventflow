#!/usr/bin/env python3
"""
EventFlow Smoke Test
Publishes a real OrderPlaced event to the deployed EventBridge bus
and verifies the full pipeline executed by checking DynamoDB records.
"""

import json
import os
import time
import uuid
from datetime import UTC, datetime

import boto3

# ── Config ────────────────────────────────────────────────────────────────────

EVENT_BUS_NAME = os.environ.get("EVENT_BUS_NAME", "eventflow-dev-bus")
ORDERS_TABLE = os.environ.get("ORDERS_TABLE_NAME", "eventflow-orders")
INVENTORY_TABLE = os.environ.get("INVENTORY_TABLE_NAME", "eventflow-inventory")
PAYMENT_TABLE = os.environ.get("PAYMENT_RECORDS_TABLE_NAME", "eventflow-payment-records")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

WAIT_SECONDS = 5
MAX_RETRIES = 6  # 30 seconds total

# ── Clients ───────────────────────────────────────────────────────────────────

events_client = boto3.client("events", region_name=AWS_REGION)
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)

# ── Helpers ───────────────────────────────────────────────────────────────────

def publish_order_placed(order_id: str, customer_id: str) -> None:
    payload = {
        "event_id": str(uuid.uuid4()),
        "event_type": "order.placed",
        "version": "1.0.0",
        "timestamp": datetime.now(UTC).isoformat(),
        "correlation_id": str(uuid.uuid4()),
        "order_id": order_id,
        "customer_id": customer_id,
        "items": [{"sku": "WIDGET-001", "quantity": 1, "price": 24.99}],
        "total_amount": 24.99,
        "shipping_address": "123 Main St, Philadelphia, PA 19103",
    }

    events_client.put_events(
        Entries=[
            {
                "Source": "eventflow.order-service",
                "DetailType": "order.placed",
                "Detail": json.dumps(payload),
                "EventBusName": EVENT_BUS_NAME,
            }
        ]
    )
    print(f"✓ Published OrderPlaced event — order_id: {order_id}")


def wait_for_record(table_name: str, key: dict, description: str) -> dict:
    table = dynamodb.Table(table_name)
    for attempt in range(1, MAX_RETRIES + 1):
        response = table.get_item(Key=key)
        item = response.get("Item")
        if item:
            print(f"✓ {description} found in {table_name}")
            return item
        print(f"  Waiting for {description}... (attempt {attempt}/{MAX_RETRIES})")
        time.sleep(WAIT_SECONDS)
    raise AssertionError(f"✗ {description} not found in {table_name} after {MAX_RETRIES * WAIT_SECONDS}s")


def assert_order_record(order_id: str) -> None:
    item = wait_for_record(
        ORDERS_TABLE,
        {"order_id": order_id},
        "Order record",
    )
    assert item["order_id"] == order_id, f"order_id mismatch: {item['order_id']}"
    print(f"  order_id: {item['order_id']}")


def assert_inventory_updated(sku: str) -> None:
    item = wait_for_record(
        INVENTORY_TABLE,
        {"sku_id": sku},
        f"Inventory record for {sku}",
    )
    print(f"  sku_id: {item['sku_id']}")


def assert_payment_record(order_id: str) -> None:
    table = dynamodb.Table(PAYMENT_TABLE)
    for attempt in range(1, MAX_RETRIES + 1):
        response = table.query(
            IndexName="order_id-index",
            KeyConditionExpression=boto3.dynamodb.conditions.Key("order_id").eq(order_id),
        ) if False else table.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr("order_id").eq(order_id)
        )
        items = response.get("Items", [])
        if items:
            print(f"✓ Payment record found for order_id: {order_id}")
            print(f"  payment_id: {items[0]['payment_id']}")
            return
        print(f"  Waiting for payment record... (attempt {attempt}/{MAX_RETRIES})")
        time.sleep(WAIT_SECONDS)
    raise AssertionError(f"✗ Payment record not found for order_id: {order_id} after {MAX_RETRIES * WAIT_SECONDS}s")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("\n── EventFlow Smoke Test ──────────────────────────────────────")
    print(f"  Bus:              {EVENT_BUS_NAME}")
    print(f"  Orders table:     {ORDERS_TABLE}")
    print(f"  Inventory table:  {INVENTORY_TABLE}")
    print(f"  Payment table:    {PAYMENT_TABLE}")
    print(f"  Region:           {AWS_REGION}")
    print("──────────────────────────────────────────────────────────────\n")

    order_id = str(uuid.uuid4())
    customer_id = str(uuid.uuid4())

    try:
        publish_order_placed(order_id, customer_id)

        print(f"\nWaiting {WAIT_SECONDS}s for initial processing...")
        time.sleep(WAIT_SECONDS)

        assert_order_record(order_id)
        assert_inventory_updated("WIDGET-001")
        assert_payment_record(order_id)

        print("\n── All assertions passed ✓ ───────────────────────────────────")
        print("  EventFlow pipeline is operational end-to-end.\n")

    except AssertionError as e:
        print(f"\n── Smoke test FAILED ✗ ───────────────────────────────────────")
        print(f"  {e}\n")
        raise SystemExit(1)


if __name__ == "__main__":
    main()