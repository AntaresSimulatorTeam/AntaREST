from unittest.mock import Mock

from antarest.core.cache.business.local_chache import LocalCache
from antarest.core.cache.business.redis_cache import RedisCache
from antarest.core.cache.main import build_cache
from antarest.core.config import Config


def test_service_factory():
    config = Config()
    cache = build_cache(config)
    assert isinstance(cache, LocalCache)

    config = Config()

    redis_client = Mock()
    cache = build_cache(config, redis_client)
    assert isinstance(cache, RedisCache)
