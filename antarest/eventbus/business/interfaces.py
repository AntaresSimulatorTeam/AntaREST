from abc import abstractmethod
from typing import List

from antarest.core.interfaces.eventbus import Event


class IEventBusBackend:
    @abstractmethod
    def push_event(self, event: Event) -> None:
        pass

    @abstractmethod
    def get_events(self) -> List[Event]:
        pass

    @abstractmethod
    def clear_events(self) -> None:
        pass
