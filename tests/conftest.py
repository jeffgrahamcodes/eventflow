from collections.abc import Callable
from typing import Any

import pytest


class TestEventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable[..., None]]] = {}
        self.published_events: list[Any] = []

    def subscribe(self, event_type: str, handler: Callable[..., None]) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def publish(self, event: Any) -> None:
        self.published_events.append(event)
        for handler in self._handlers.get(event.event_type, []):
            handler(event)


@pytest.fixture
def bus() -> TestEventBus:
    return TestEventBus()
