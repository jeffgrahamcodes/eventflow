from eventflow.bus import EventBus
from eventflow.events import OrderValidated, OrderCancelled

class InventoryService:
    def __init__(self, bus: EventBus) -> None:
        self.bus = bus
        self.bus.subscribe("order.validated", self.reserve_stock)
        self.bus.subscribe("order.cancelled", self.release_stock)
        self._inventory: dict[str, int] = {
            "WIDGET-001": 50, 
            "WIDGET-002": 12, 
            "WIDGET-003": 25,
            "WIDGET-005": 0,
            }

    def reserve_stocke(self, event: OrderValidated):
        pass

    def release_stocke(self, event: OrderCancelled):
        pass