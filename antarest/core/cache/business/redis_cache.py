import json
from typing import Optional, Any, List
import redis
from pydantic import BaseModel
from redis.client import Redis
from antarest.core.config import RedisConfig
from antarest.core.interfaces.cache import ICache


class RedisCacheElement(BaseModel):
    duration: int
    data: Any


class RedisCache(ICache):
    def __init__(
        self, config: RedisConfig, redis_client: Optional[Redis] = None
    ):
        self.redis = (
            redis_client
            if redis_client is not None
            else redis.Redis(host=config.host, port=config.port, db=0)
        )

    def start(self):
        pass

    def put(self, id: str, data: Any, duration: int = 3600) -> None:
        redis_element = RedisCacheElement(duration=duration, data=data)
        redis_key = f"cache:{id}"
        print(
            f"************************** PUT : {redis_key} => {redis_element}"
        )
        self.redis.set(redis_key, redis_element.json())
        self.redis.expire(redis_key, duration)

    def get(self, id: str, refresh_timeout: Optional[int] = None) -> Any:
        redis_key = f"cache:{id}"
        result = self.redis.get(redis_key)
        path = id.split("/")
        if result is not None:
            json_result = json.loads(result)
            redis_element = RedisCacheElement(
                duration=json_result["duration"], data=json_result["data"]
            )
            print(
                f"************************** GET IN CACHE : {redis_key} => {redis_element}"
            )
            self.redis.expire(redis_key, redis_element.duration)
            return redis_element.data
        return None

    def invalidate(self, id: str) -> None:
        return self.redis.delete(f"cache:{id}")

    def invalidate_all(self, ids: List[str]) -> None:
        return self.redis.delete(*[f"cache:{id}" for id in ids])
