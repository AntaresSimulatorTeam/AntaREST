import logging
from typing import List, Dict, Optional

from antarest.core.interfaces.eventbus import Event
from antarest.eventbus.business.interfaces import IEventBusBackend

logger = logging.getLogger(__name__)


class LocalEventBus(IEventBusBackend):
    def __init__(self) -> None:
        self.events: List[Event] = []
        self.queues: Dict[str, List[Event]] = {}

    def push_event(self, event: Event) -> None:
        self.events.append(event)

    def get_events(self) -> List[Event]:
        return self.events

    def clear_events(self) -> None:
        self.events.clear()

    def queue_event(self, event: Event, queue: str) -> None:
        if queue not in self.queues:
            self.queues[queue] = []
        self.queues[queue].append(event)

    def pull_queue(self, queue: str) -> Optional[Event]:
        if queue in self.queues and len(self.queues) > 0:
            return self.queues[queue].pop(0)
        return None
