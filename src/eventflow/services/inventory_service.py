from eventflow.bus import EventBus
from eventflow.events import (
    OrderCancelled,
    OrderValidated,
    StockInsufficient,
    StockReserved,
)


class InventoryService:
    def __init__(self, bus: EventBus) -> None:
        self.bus = bus
        self.bus.subscribe("order.validated", self.reserve_stock)
        self.bus.subscribe("order.cancelled", self.release_stock)
        self._inventory: dict[str, int] = {
            "WIDGET-001": 50, 
            "WIDGET-002": 12, 
            "WIDGET-003": 25,
            "WIDGET-OOS": 0,
            }
        
    def reserve_stock(self, event: OrderValidated) -> None:
        available_quantities = []
        insufficient_items = []
        
        for item in event.items:
            sku = item["sku"]
            quantity = item["quantity"]
            available = self._inventory.get(sku, 0)
            
            if available < quantity:
                insufficient_items.append({"sku": sku, "quantity": quantity})
                available_quantities.append({"sku": sku, "available": available})

        if insufficient_items:
            self.bus.publish(
                StockInsufficient(
                    order_id=event.order_id,
                    customer_id=event.customer_id,
                    correlation_id=event.correlation_id,
                    insufficient_items=insufficient_items,
                    available_quantities=available_quantities,
                )
            )
            return
        
        # All items available — reserve them
        reserved_items = []
        for item in event.items:
            sku = item["sku"]
            quantity = item["quantity"]
            self._inventory[sku] -= quantity
            reserved_items.append({"sku": sku, "quantity": quantity})

        self.bus.publish(
            StockReserved(
                order_id=event.order_id,
                customer_id=event.customer_id,
                correlation_id=event.correlation_id,
                reserved_items=reserved_items,
            )
        )
        
    def release_stock(self, event: OrderCancelled) -> None:
        pass