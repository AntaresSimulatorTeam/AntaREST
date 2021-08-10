import threading
import time
from typing import Optional, Dict, Any, List

from pydantic import BaseModel

from antarest.core.config import CacheConfig
from antarest.core.interfaces.cache import ICache


class LocalCacheElement(BaseModel):
    timeout: int
    duration: int
    data: Any


class LocalCache(ICache):
    def __init__(self, config: CacheConfig):
        self.cache: Dict[str, LocalCacheElement] = dict()
        self.lock = threading.Lock()
        self.checker_delay = config.checker_delay
        self.checker_thread = threading.Thread(
            target=self.checker, daemon=True
        )

    def start(self):
        self.checker_thread.start()

    def checker(self):
        while True:
            time.sleep(self.checker_delay)
            with self.lock:
                current_time = time.time()
                for id in self.cache.keys():
                    if current_time >= self.cache[id].timeout:
                        print(f"DELETE  {id} from cache")
                        del self.cache[
                            id
                        ]  # Python 3 allow us to delete items while iterating a dictionary

    def put(
        self, id: str, data: Any, duration: int = 3600
    ) -> None:  # Duration in second
        with self.lock:
            self.cache[id] = LocalCacheElement(
                data=data,
                timeout=(time.time() + duration),
                duration=duration,
            )

    def get(self, id: str, refresh_duration: Optional[int] = None) -> Any:
        res = None
        with self.lock:
            if id in self.cache:
                if refresh_duration:
                    self.cache[id].duration = refresh_duration
                self.cache[id].timeout = time.time() + self.cache[id].duration
                res = self.cache[id]
        return res

    def invalidate(self, id: str) -> None:
        with self.lock:
            if id in self.cache:
                del self.cache[id]

    def invalidate_all(self, ids: List[str]) -> None:
        with self.lock:
            for id in ids:
                if id in self.cache:
                    del self.cache[id]
