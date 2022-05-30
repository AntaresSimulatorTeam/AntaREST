import asyncio
import logging
import random
import threading
import time
from typing import List, Callable, Optional, Dict, Awaitable, Any, cast
from uuid import uuid4

from antarest.core.interfaces.eventbus import Event, IEventBus, EventType
from antarest.core.utils.utils import suppress_exception
from antarest.eventbus.business.interfaces import IEventBusBackend

logger = logging.getLogger(__name__)


class EventBusService(IEventBus):
    def __init__(
        self, backend: IEventBusBackend, autostart: bool = True
    ) -> None:
        self.backend = backend
        self.listeners: Dict[
            EventType, Dict[str, Callable[[Event], Awaitable[None]]]
        ] = {ev_type: {} for ev_type in EventType}
        self.consumers: Dict[
            str, Dict[str, Callable[[Event], Awaitable[None]]]
        ] = {}

        self.lock = threading.Lock()
        if autostart:
            self.start()

    def push(self, event: Event) -> None:
        self.backend.push_event(event)

    def queue(self, event: Event, queue: str) -> None:
        self.backend.queue_event(event, queue)

    def add_queue_consumer(
        self, listener: Callable[[Event], Awaitable[None]], queue: str
    ) -> str:
        with self.lock:
            listener_id = str(uuid4())
            if queue not in self.consumers:
                self.consumers[queue] = {}
            self.consumers[queue][listener_id] = listener
            return listener_id

    def remove_queue_consumer(self, listener_id: str) -> None:
        with self.lock:
            for queue in self.consumers:
                if listener_id in self.consumers[queue]:
                    del self.consumers[queue][listener_id]

    def add_listener(
        self,
        listener: Callable[[Event], Awaitable[None]],
        type_filter: Optional[List[EventType]] = None,
    ) -> str:
        with self.lock:
            listener_id = str(uuid4())
            types = type_filter or [EventType.ANY]
            for listener_type in types:
                self.listeners[listener_type][listener_id] = listener
            return listener_id

    def remove_listener(self, listener_id: str) -> None:
        with self.lock:
            for listener_type in self.listeners:
                if listener_id in self.listeners[listener_type]:
                    del self.listeners[listener_type][listener_id]

    async def _run_loop(self) -> None:
        while True:
            time.sleep(0.2)
            try:
                await self._on_events()
            except Exception as e:
                logger.error(
                    f"Unexpected error when processing events", exc_info=e
                )

    async def _on_events(self) -> None:
        with self.lock:
            for queue in self.consumers:
                if len(self.consumers[queue]) > 0:
                    event = self.backend.pull_queue(queue)
                    while event is not None:
                        try:
                            await list(self.consumers[queue].values())[
                                random.randint(
                                    0, len(self.consumers[queue]) - 1
                                )
                            ](event)
                        except Exception as ex:
                            logger.error(
                                f"Failed to process queue event {event.type}",
                                exc_info=ex,
                            )
                        event = self.backend.pull_queue(queue)

            for e in self.backend.get_events():
                if e.type in self.listeners:
                    responses = await asyncio.gather(
                        *[
                            listener(e)
                            for listener in list(
                                self.listeners[e.type].values()
                            )
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

    def _async_loop(self, new_loop: bool = True) -> None:
        loop = (
            asyncio.new_event_loop() if new_loop else asyncio.get_event_loop()
        )
        loop.run_until_complete(self._run_loop())

    def start(self, threaded: bool = True) -> None:
        if threaded:
            t = threading.Thread(target=self._async_loop)
            t.setDaemon(True)
            logger.info("Starting event bus")
            t.start()
        else:
            self._async_loop(new_loop=False)
