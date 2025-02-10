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

import asyncio
import logging
import random
import threading
import uuid
from typing import Awaitable, Callable, Dict, List, Optional

from typing_extensions import override

from antarest.core.interfaces.eventbus import Event, EventType, IEventBus
from antarest.eventbus.business.interfaces import IEventBusBackend

logger = logging.getLogger(__name__)


EVENT_LOOP_REST_TIME = 0.2


class EventBusService(IEventBus):
    def __init__(self, backend: IEventBusBackend, autostart: bool = True) -> None:
        self.backend = backend
        self.listeners: Dict[EventType, Dict[str, Callable[[Event], Awaitable[None]]]] = {
            ev_type: {} for ev_type in EventType
        }
        self.consumers: Dict[str, Dict[str, Callable[[Event], Awaitable[None]]]] = {}

        self.lock = threading.Lock()
        if autostart:
            self.start()

    @override
    def push(self, event: Event) -> None:
        self.backend.push_event(event)

    @override
    def queue(self, event: Event, queue: str) -> None:
        self.backend.queue_event(event, queue)

    @override
    def add_queue_consumer(self, listener: Callable[[Event], Awaitable[None]], queue: str) -> str:
        with self.lock:
            listener_id = str(uuid.uuid4())
            if queue not in self.consumers:
                self.consumers[queue] = {}
            self.consumers[queue][listener_id] = listener
            return listener_id

    @override
    def remove_queue_consumer(self, listener_id: str) -> None:
        with self.lock:
            for queue in self.consumers:
                if listener_id in self.consumers[queue]:
                    del self.consumers[queue][listener_id]

    @override
    def add_listener(
        self,
        listener: Callable[[Event], Awaitable[None]],
        type_filter: Optional[List[EventType]] = None,
    ) -> str:
        with self.lock:
            listener_id = str(uuid.uuid4())
            types = type_filter or [EventType.ANY]
            for listener_type in types:
                self.listeners[listener_type][listener_id] = listener
            return listener_id

    @override
    def remove_listener(self, listener_id: str) -> None:
        with self.lock:
            for listener_type in self.listeners:
                if listener_id in self.listeners[listener_type]:
                    del self.listeners[listener_type][listener_id]

    async def _run_loop(self) -> None:
        while True:
            try:
                processed_events_count = await self._on_events()
                # Give the loop some rest if it has nothing to do
                if processed_events_count == 0:
                    await asyncio.sleep(EVENT_LOOP_REST_TIME)
            except Exception as e:
                logger.error("Unexpected error when processing events", exc_info=e)

    async def _on_events(self) -> int:
        processed_events_count = 0
        with self.lock:
            for queue in self.consumers:
                if len(self.consumers[queue]) > 0:
                    event = self.backend.pull_queue(queue)
                    while event is not None:
                        processed_events_count += 1
                        try:
                            await list(self.consumers[queue].values())[
                                random.randint(0, len(self.consumers[queue]) - 1)
                            ](event)
                        except Exception as ex:
                            logger.error(
                                f"Failed to process queue event {event.type}",
                                exc_info=ex,
                            )
                        event = self.backend.pull_queue(queue)

            events = self.backend.get_events()
            processed_events_count += len(events)
            for e in events:
                if e.type in self.listeners:
                    responses = await asyncio.gather(
                        *[
                            listener(e)
                            for listener in list(self.listeners[e.type].values())
                            + list(self.listeners[EventType.ANY].values())
                        ]
                    )
                    for res in responses:
                        if isinstance(res, Exception):
                            logger.error(
                                f"Failed to process event {e.type}",
                                exc_info=res,
                            )
            self.backend.clear_events()
            return processed_events_count

    def _async_loop(self, new_loop: bool = True) -> None:
        loop = asyncio.new_event_loop() if new_loop else asyncio.get_event_loop()
        loop.run_until_complete(self._run_loop())

    @override
    def start(self, threaded: bool = True) -> None:
        if threaded:
            t = threading.Thread(
                target=self._async_loop,
                name=self.__class__.__name__,
                daemon=True,
            )
            logger.info("Starting event bus")
            t.start()
        else:
            self._async_loop(new_loop=False)
