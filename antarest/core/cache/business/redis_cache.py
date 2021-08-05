from typing import Optional

from antarest.core.config import RedisConfig
from antarest.core.custom_types import JSON
from antarest.core.interfaces.cache import ICache


class RedisCache(ICache):
    def __init__(self, config: RedisConfig):
        self.config = config

    def start(self):
        pass

    def put(self, id: str, data: JSON, timeout: int = 600000) -> None:
        pass

    def get(
        self, id: str, refresh_timeout: Optional[int] = None
    ) -> Optional[JSON]:
        pass

    def invalidate(self, id: str) -> None:
        pass
