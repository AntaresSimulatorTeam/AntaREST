import threading
import time
from typing import Optional, Dict, Any

from pydantic import BaseModel

from antarest.core.custom_types import JSON
from antarest.core.interfaces.cache import ICache


class CacheElement(BaseModel):
    timeout: int
    duration: int
    data: Any


class LocalCache(ICache):
    def __init__(self):
        self.cache: Dict[str, CacheElement] = dict()
        self.checker_thread = None
        self.checker_thread = threading.Thread(
            target=self.checker, daemon=True, args=(0.2,)
        )

    def start(self):
        self.checker_thread.start()

    def checker(self, delay: float):
        while True:
            time.sleep(delay)
            current_time = time.time()
            for id in self.cache.keys():
                if current_time >= self.cache[id].timeout:
                    del self.cache[
                        id
                    ]  # Python 3 allow us to delete items while iterating a dictionary

    def put(
        self, id: str, data: Any, duration: int = 3600
    ) -> None:  # Duration in second
        print(f"PUT {id} in cache")
        self.cache[id] = CacheElement(
            data=data,
            timeout=(time.time() + duration),
            duration=duration,
        )

    def get(self, id: str, refresh_duration: Optional[int] = None) -> Any:
        print(f"GET {id} in cache")
        if id in self.cache:
            if refresh_duration:
                self.cache[id].duration = refresh_duration
            self.cache[id].timeout = time.time() + self.cache[id].duration
            return self.cache[id]
        return None

    def invalidate(self, id: str) -> None:
        if id in self.cache[id]:
            del self.cache[id]
