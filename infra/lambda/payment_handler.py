import json
import os
from typing import Any

import boto3

from eventflow.bus import EventBus
from eventflow.events import OrderCancelled, PaymentCharged, StockReserved
from eventflow.services.payment_service import PaymentService

secrets_client = boto3.client("secretsmanager")


def get_payment_credentials() -> dict:
    secret_arn = os.environ["PAYMENT_SECRET_ARN"]
    response = secrets_client.get_secret_value(SecretId=secret_arn)
    return json.loads(response["SecretString"])


payment_credentials = get_payment_credentials()


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
