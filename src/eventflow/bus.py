from collections.abc import Callable
from typing import Any


class EventBus:
    def subscribe(self, event_type: str, handler: Callable[..., None]) -> None:
        pass

    def publish(self, event: Any) -> None:
        pass
