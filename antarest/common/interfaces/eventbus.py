from abc import ABC, abstractmethod
from typing import Any, Callable, Optional, List, Awaitable

from dataclasses import dataclass


class EventType:
    STUDY_CREATED = "STUDY_CREATED"
    STUDY_DELETED = "STUDY_DELETED"
    STUDY_EDITED = "STUDY_EDITED"
    STUDY_JOB_STARTED = "STUDY_JOB_STARTED"
    STUDY_JOB_LOG_UPDATE = "STUDY_JOB_LOG_UPDATE"
    STUDY_JOB_COMPLETED = "STUDY_JOB_COMPLETED"
    STUDY_JOB_STATUS_UPDATE = "STUDY_JOB_STATUS_UPDATE"


@dataclass
class Event:
    type: str
    payload: Any


class IEventBus(ABC):
    @abstractmethod
    def push(self, event: Event) -> None:
        pass

    @abstractmethod
    def add_listener(
        self,
        listener: Callable[[Event], Awaitable[None]],
        type_filter: Optional[List[str]] = None,
    ) -> str:
        """
        Add an event listener listener
        @param listener listener callback
        @param type_filter list of event types to listen to (or None to catch all)

        Beware of the fact that in gunicorn, listeners will be called on the same event as many as there is workers
        """
        pass

    @abstractmethod
    def remove_listener(self, listener_id: str) -> None:
        pass

    @abstractmethod
    def start(self, threaded: bool = True) -> None:
        pass


class DummyEventBusService(IEventBus):
    def push(self, event: Event) -> None:
        # Noop
        pass

    def add_listener(
        self,
        listener: Callable[[Event], Awaitable[None]],
        type_filter: Optional[List[str]] = None,
    ) -> str:
        return ""

    def remove_listener(self, listener_id: str) -> None:
        # Noop
        pass

    def start(self, threaded: bool = True) -> None:
        # Noop
        pass
