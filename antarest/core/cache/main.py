import logging
from typing import Optional

from redis import Redis

from antarest.core.cache.business.local_chache import LocalCache
from antarest.core.cache.business.redis_cache import RedisCache
from antarest.core.config import Config
from antarest.core.interfaces.cache import ICache

logger = logging.getLogger(__name__)


def build_cache(
    config: Config, redis_client: Optional[Redis] = None
) -> ICache:
    cache_conf = config.cache
    redis_conf = config.redis
    cache = (
        RedisCache(config=redis_conf, redis_client=redis_client)
        if redis_conf is not None
        else LocalCache(config=cache_conf)
    )

    logger.info("Redis cache" if redis_conf is not None else "Local cache")
    cache.start()
    return cache
