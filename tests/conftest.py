from collections.abc import Callable
from typing import Any

import pytest

from eventflow.bus import EventBus


class FakeEventBus(EventBus):
    def __init__(self) -> None:
        super().__init__()
        self.published_events: list[Any] = []

    def publish(self, event: Any) -> None:
        self.published_events.append(event)
        super().publish(event)

@pytest.fixture
def bus() -> FakeEventBus:
    return FakeEventBus()
