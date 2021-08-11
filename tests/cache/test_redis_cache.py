import json
from pathlib import Path
from unittest.mock import Mock
from antarest.core.cache.business.redis_cache import (
    RedisCache,
    RedisCacheElement,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
    Area,
)


def test_lifecycle():
    redis_client = Mock()
    cache = RedisCache(redis_client)
    config = FileStudyTreeConfig(
        study_path=Path("somepath"),
        path=Path("somepath"),
        study_id="",
        version=-1,
        areas={
            "a1": Area(
                links={},
                thermals=[],
                renewables=[],
                filters_synthesis=[],
                filters_year=[],
            )
        },
    )
    id = "some_id"
    redis_key = f"cache:{id}"
    duration = 3600
    cache_element = RedisCacheElement(
        duration=duration, data=config.dict()
    ).json()

    # GET
    redis_client.get.return_value = cache_element
    load = json.loads(cache_element)
    assert cache.get(id=id) == load["data"]
    redis_client.expire.assert_called_with(redis_key, duration)
    redis_client.get.assert_called_once_with(redis_key)

    # PUT
    duration = 7200
    cache_element = RedisCacheElement(
        duration=duration, data=config.dict()
    ).json()
    cache.put(id=id, data=config.dict(), duration=duration)
    redis_client.set.assert_called_once_with(redis_key, cache_element)
    redis_client.expire.assert_called_with(redis_key, duration)
