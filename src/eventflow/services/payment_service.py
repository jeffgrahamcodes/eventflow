from eventflow.bus import EventBus
from eventflow.events import OrderCancelled, StockReserved


class PaymentService:
    def __init__(self, bus: EventBus) -> None:
        self.bus = bus
        self.bus.subscribe("stock.reserved", self.charge)
        self.bus.subscribe("order.cancelled", self.refund)
        self.should_fail: bool

    def charge(self, event: StockReserved) -> None:
        pass

    def refund(self, event: OrderCancelled) -> None:
        pass
