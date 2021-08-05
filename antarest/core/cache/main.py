from antarest.core.cache.business.local_chache import LocalCache
from antarest.core.cache.business.redis_cache import RedisCache
from antarest.core.config import Config
from antarest.core.interfaces.cache import ICache


def build_cache(
    config: Config,
) -> ICache:
    redis_conf = config.eventbus.redis
    cache = (
        RedisCache(config=redis_conf)
        if redis_conf is not None
        else LocalCache()
    )

    print("LOCAL" if redis_conf is not None else "REDIS")
    cache.start()
    return cache
