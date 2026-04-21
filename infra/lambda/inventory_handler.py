import json
from typing import Any

from eventflow.bus import EventBus
from eventflow.events import (
    OrderCancelled,
    OrderValidated,
)
from eventflow.services.inventory_service import InventoryService

bus = EventBus()
inventory_service = InventoryService(bus)


def handler(event: dict[str, Any], context: Any) -> None:
    for record in event["Records"]:
        body = json.loads(record["body"])
        detail_type = body["detail-type"]
        detail = body["detail"]

        if detail_type == "order.validated":
            event_obj = OrderValidated.model_validate(detail)
            inventory_service.reserve_stock(event_obj)
        elif detail_type == "order.cancelled":
            event_obj = OrderCancelled.model_validate(detail)
            inventory_service.release_stock(event_obj)
