import asyncio
import logging
import threading
import time
from typing import List, Callable, Optional, Dict, Awaitable
from uuid import uuid4

from antarest.core.interfaces.eventbus import Event, IEventBus
from antarest.eventbus.business.interfaces import IEventBusBackend

logger = logging.getLogger(__name__)


class EventBusService(IEventBus):
    def __init__(
        self, backend: IEventBusBackend, autostart: bool = True
    ) -> None:
        self.backend = backend
        self.listeners: Dict[str, Callable[[Event], Awaitable[None]]] = {}
        self.lock = threading.Lock()
        if autostart:
            self.start()

    def push(self, event: Event) -> None:
        self.backend.push_event(event)

    def add_listener(
        self,
        listener: Callable[[Event], Awaitable[None]],
        type_filter: Optional[List[str]] = None,
    ) -> str:
        with self.lock:
            listener_id = str(uuid4())
            self.listeners[listener_id] = listener
            return listener_id

    def remove_listener(self, listener_id: str) -> None:
        with self.lock:
            del self.listeners[listener_id]

    async def _run_loop(self) -> None:
        while True:
            time.sleep(0.2)
            await self._on_events()

    async def _on_events(self) -> None:
        with self.lock:
            for e in self.backend.get_events():
                for listener in self.listeners.values():
                    try:
                        await listener(e)
                    except Exception as ex:
                        logger.error(
                            f"Failed to process event {e.type}", exc_info=ex
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
