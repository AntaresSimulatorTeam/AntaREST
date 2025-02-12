# Copyright (c) 2025, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Any, Awaitable, Callable, List, Optional

from typing_extensions import override

from antarest.core.model import PermissionInfo
from antarest.core.serde import AntaresBaseModel


class EventType(StrEnum):
    ANY = "_ANY"
    STUDY_CREATED = "STUDY_CREATED"
    STUDY_DELETED = "STUDY_DELETED"
    STUDY_EDITED = "STUDY_EDITED"
    STUDY_DATA_EDITED = "STUDY_DATA_EDITED"
    STUDY_JOB_STARTED = "STUDY_JOB_STARTED"
    STUDY_JOB_LOG_UPDATE = "STUDY_JOB_LOG_UPDATE"
    STUDY_JOB_COMPLETED = "STUDY_JOB_COMPLETED"
    STUDY_JOB_STATUS_UPDATE = "STUDY_JOB_STATUS_UPDATE"
    STUDY_JOB_CANCEL_REQUEST = "STUDY_JOB_CANCEL_REQUEST"
    STUDY_JOB_CANCELLED = "STUDY_JOB_CANCELLED"
    STUDY_VARIANT_GENERATION_COMMAND_RESULT = "STUDY_VARIANT_GENERATION_COMMAND_RESULT"
    TASK_ADDED = "TASK_ADDED"
    TASK_RUNNING = "TASK_RUNNING"
    TASK_PROGRESS = "TASK_PROGRESS"
    TASK_COMPLETED = "TASK_COMPLETED"
    TASK_FAILED = "TASK_FAILED"
    TASK_CANCEL_REQUEST = "TASK_CANCEL_REQUEST"
    DOWNLOAD_CREATED = "DOWNLOAD_CREATED"
    DOWNLOAD_READY = "DOWNLOAD_READY"
    DOWNLOAD_EXPIRED = "DOWNLOAD_EXPIRED"
    DOWNLOAD_FAILED = "DOWNLOAD_FAILED"
    MESSAGE_INFO = "MESSAGE_INFO"
    MAINTENANCE_MODE = "MAINTENANCE_MODE"
    WORKER_TASK = "WORKER_TASK"
    WORKER_TASK_STARTED = "WORKER_TASK_STARTED"
    WORKER_TASK_ENDED = "WORKER_TASK_ENDED"
    LAUNCH_PROGRESS = "LAUNCH_PROGRESS"


class EventChannelDirectory:
    JOB_STATUS = "JOB_STATUS/"
    JOB_LOGS = "JOB_LOGS/"
    TASK = "TASK/"
    STUDY_GENERATION = "GENERATION_TASK/"


class Event(AntaresBaseModel):
    type: EventType
    payload: Any
    permissions: PermissionInfo
    channel: str = ""


EventListener = Callable[[Event], Awaitable[None]]


class IEventBus(ABC):
    """
    Interface for the event bus.

    The event bus provides 2 communication mechanisms:
      - a broadcasting mechanism, where events are pushed to all
        registered listeners
      - a message queue mechanism: a message can be pushed to
        a specified queue. Only consumers registered for that
        queue will be called to handle those messages.
    """

    @abstractmethod
    def push(self, event: Event) -> None:
        """
        Pushes an event to registered listeners.
        """
        pass

    @abstractmethod
    def queue(self, event: Event, queue: str) -> None:
        """
        Queues an event at the end of the specified queue.
        """
        pass

    @abstractmethod
    def add_queue_consumer(self, listener: EventListener, queue: str) -> str:
        """
        Adds a consumer for events on the specified queue.
        """
        pass

    @abstractmethod
    def remove_queue_consumer(self, listener_id: str) -> None:
        pass

    @abstractmethod
    def add_listener(
        self,
        listener: EventListener,
        type_filter: Optional[List[EventType]] = None,
    ) -> str:
        """
        Add a new event listener in the event bus.

        The listener can listen to several types of events, depending on the filter
        list. If not specified, the listener will listen to all event types.

        Note:
            Be aware that in `gunicorn`, the listeners will be called on the same
            event as many times as there are workers.

        Args:
            listener: callback of the listener
            type_filter: list of event types to listen to (or `None` to catch everything).

        Returns:
            Listener registration ID (usually a UUID).
        """

    @abstractmethod
    def remove_listener(self, listener_id: str) -> None:
        pass

    @abstractmethod
    def start(self, threaded: bool = True) -> None:
        pass


class DummyEventBusService(IEventBus):
    def __init__(self) -> None:
        self.events: List[Event] = []

    @override
    def queue(self, event: Event, queue: str) -> None:
        # Noop
        pass

    @override
    def add_queue_consumer(self, listener: Callable[[Event], Awaitable[None]], queue: str) -> str:
        return ""

    @override
    def remove_queue_consumer(self, listener_id: str) -> None:
        # Noop
        pass

    @override
    def push(self, event: Event) -> None:
        # Noop
        self.events.append(event)

    @override
    def add_listener(
        self,
        listener: Callable[[Event], Awaitable[None]],
        type_filter: Optional[List[EventType]] = None,
    ) -> str:
        return ""

    @override
    def remove_listener(self, listener_id: str) -> None:
        # Noop
        pass

    @override
    def start(self, threaded: bool = True) -> None:
        # Noop
        pass
