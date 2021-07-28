import logging
from typing import List

from antarest.core.interfaces.eventbus import Event
from antarest.eventbus.business.interfaces import IEventBusBackend

logger = logging.getLogger(__name__)


class LocalEventBus(IEventBusBackend):
    def __init__(self) -> None:
        self.events: List[Event] = []

    def push_event(self, event: Event) -> None:
        self.events.append(event)

    def get_events(self) -> List[Event]:
        return self.events

    def clear_events(self) -> None:
        self.events.clear()
