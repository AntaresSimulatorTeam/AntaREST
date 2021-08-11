from antarest.core.cache.business.local_chache import LocalCache
from antarest.core.cache.business.redis_cache import RedisCache
from antarest.core.cache.main import build_cache
from antarest.core.config import Config, RedisConfig


def test_service_factory():
    config = Config()
    cache = build_cache(config)
    assert isinstance(cache, LocalCache)

    config = Config(redis=RedisConfig(host="localhost"))

    cache = build_cache(config)
    assert isinstance(cache, RedisCache)
