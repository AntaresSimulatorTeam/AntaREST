import abc
from abc import abstractmethod
from typing import List, Optional

from antarest.core.interfaces.eventbus import Event


class IEventBusBackend(abc.ABC):
    @abstractmethod
    def push_event(self, event: Event) -> None:
        raise NotImplementedError

    @abstractmethod
    def queue_event(self, event: Event, queue: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def pull_queue(self, queue: str) -> Optional[Event]:
        raise NotImplementedError

    @abstractmethod
    def get_events(self) -> List[Event]:
        raise NotImplementedError

    @abstractmethod
    def clear_events(self) -> None:
        raise NotImplementedError
