import json
from typing import Optional, List
from pydantic import BaseModel
from redis.client import Redis
from antarest.core.custom_types import JSON
from antarest.core.interfaces.cache import ICache


class RedisCacheElement(BaseModel):
    duration: int
    data: JSON


class RedisCache(ICache):
    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    def start(self) -> None:
        pass

    def put(self, id: str, data: JSON, duration: int = 3600) -> None:
        redis_element = RedisCacheElement(duration=duration, data=data)
        redis_key = f"cache:{id}"
        self.redis.set(redis_key, redis_element.json())
        self.redis.expire(redis_key, duration)

    def get(
        self, id: str, refresh_timeout: Optional[int] = None
    ) -> Optional[JSON]:
        redis_key = f"cache:{id}"
        result = self.redis.get(redis_key)
        if result is not None:
            json_result = json.loads(result)
            redis_element = RedisCacheElement(
                duration=json_result["duration"], data=json_result["data"]
            )
            self.redis.expire(
                redis_key,
                redis_element.duration
                if refresh_timeout is None
                else refresh_timeout,
            )
            return redis_element.data
        return None

    def invalidate(self, id: str) -> None:
        self.redis.delete(f"cache:{id}")

    def invalidate_all(self, ids: List[str]) -> None:
        self.redis.delete(*[f"cache:{id}" for id in ids])
