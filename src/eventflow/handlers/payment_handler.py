import json
import os
from decimal import Decimal
from typing import Any

import boto3

from eventflow.events import (
    OrderCancelled,
    PaymentCharged,
    PaymentFailed,
    PaymentFailureReason,
    PaymentRefunded,
    StockReserved,
)

dynamodb = boto3.resource("dynamodb")
payment_table = dynamodb.Table(os.environ["PAYMENT_RECORDS_TABLE_NAME"])
events_client = boto3.client("events")
secrets_client = boto3.client("secretsmanager")
EVENT_BUS_NAME = os.environ.get("EVENT_BUS_NAME", "eventflow-dev-bus")

_pending_charges: dict[str, Decimal] = {}


def get_payment_credentials() -> dict:
    secret_arn = os.environ["PAYMENT_SECRET_ARN"]
    response = secrets_client.get_secret_value(SecretId=secret_arn)
    return json.loads(response["SecretString"])


payment_credentials = get_payment_credentials()


def publish(event_obj) -> None:
    events_client.put_events(Entries=[{
        "Source": "eventflow.payment-service",
        "DetailType": event_obj.event_type,
        "Detail": event_obj.model_dump_json(),
        "EventBusName": EVENT_BUS_NAME,
    }])


def handler(event: dict[str, Any], context: Any) -> None:
    for record in event["Records"]:
        body = json.loads(record["body"])
        detail_type = body["detail-type"]
        detail = body["detail"]

        if detail_type == "stock.reserved":
            event_obj = StockReserved.model_validate(detail)
            charge_amount = Decimal(str(event_obj.total_amount))
            order_id = str(event_obj.order_id)

            charged = PaymentCharged(
                order_id=event_obj.order_id,
                customer_id=event_obj.customer_id,
                correlation_id=event_obj.correlation_id,
                charge_amount=event_obj.total_amount,
                payment_method_last_four="1234",
            )

            payment_table.put_item(Item={
                "payment_id": str(charged.event_id),
                "order_id": order_id,
                "charge_amount": charge_amount,
                "status": "charged",
            })

            _pending_charges[order_id] = charge_amount
            publish(charged)

        elif detail_type == "order.cancelled":
            event_obj = OrderCancelled.model_validate(detail)
            order_id = str(event_obj.order_id)
            refund_amount = _pending_charges.pop(order_id, None)

            if refund_amount is not None:
                publish(PaymentRefunded(
                    order_id=event_obj.order_id,
                    customer_id=event_obj.customer_id,
                    correlation_id=event_obj.correlation_id,
                    refund_amount=float(refund_amount),
                ))

        elif detail_type == "payment.charged":
            order_id = str(detail["order_id"])
            _pending_charges[order_id] = Decimal(str(detail["charge_amount"]))