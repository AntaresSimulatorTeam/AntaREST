import io
import json
import pickle
from typing import Optional, Any, List
import redis
from pydantic import BaseModel
from redis.client import Redis
from antarest.core.config import RedisConfig
from antarest.core.interfaces.cache import ICache
from antarest.study.storage.rawstudy.model import FileStudyTreeConfig


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
        print(f"************************** PUT : {redis_key}")
        if not isinstance(data, tuple):
            self.redis.set(redis_key, redis_element.json())
            self.redis.expire(redis_key, duration)
        else:
            (config, tree) = data
            # container = io.BytesIO()
            # pickle.dump(data, container)
            # container.seek(0)
            # print(f'************************** TUPLE : {redis_key}, config : {container}')

    def get(self, id: str, refresh_timeout: Optional[int] = None) -> Any:
        redis_key = f"cache:{id}"
        result = self.redis.get(redis_key)
        if result is not None:
            json_result = result  # json.loads(result)
            # result.expire(redis_key, duration)
            print(f"************************** REDIS RESULT: {json_result}")
        print(f"************************** GET IS NONE")
        return None

    def invalidate(self, id: str) -> None:
        return self.redis.delete(f"cache:{id}")

    def invalidate_all(self, ids: List[str]) -> None:
        return self.redis.delete(*[f"cache:{id}" for id in ids])
