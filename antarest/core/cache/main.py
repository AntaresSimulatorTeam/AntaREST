from antarest.core.cache.business.local_chache import LocalCache
from antarest.core.cache.business.redis_cache import RedisCache
from antarest.core.config import Config
from antarest.core.interfaces.cache import ICache


def build_cache(
    config: Config,
) -> ICache:
    cache_conf = config.cache
    redis_conf = config.cache.redis
    cache = (
        RedisCache(config=redis_conf)
        if redis_conf is not None
        else LocalCache(config=cache_conf)
    )

    print(
        "************************** REDIS"
        if redis_conf is not None
        else "************************** LOCAL"
    )
    cache.start()
    return cache
