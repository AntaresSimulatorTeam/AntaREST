# Copyright (c) 2025, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import logging
from typing import List, Optional

from redis.client import Redis
from typing_extensions import override

from antarest.core.interfaces.cache import ICache
from antarest.core.model import JSON
from antarest.core.serde import AntaresBaseModel
from antarest.core.serde.json import from_json

logger = logging.getLogger(__name__)


class RedisCacheElement(AntaresBaseModel):
    duration: int
    data: JSON


class RedisCache(ICache):
    def __init__(self, redis_client: Redis):  # type: ignore
        self.redis = redis_client

    @override
    def start(self) -> None:
        # Assuming the Redis service is already running; no need to start it here.
        pass

    @override
    def put(self, id: str, data: JSON, duration: int = 3600) -> None:
        redis_element = RedisCacheElement(duration=duration, data=data)
        redis_key = f"cache:{id}"
        logger.info(f"Adding cache key {id}")
        self.redis.set(redis_key, redis_element.model_dump_json())
        self.redis.expire(redis_key, duration)

    @override
    def get(self, id: str, refresh_timeout: Optional[int] = None) -> Optional[JSON]:
        redis_key = f"cache:{id}"
        result = self.redis.get(redis_key)
        logger.info(f"Trying to retrieve cache key {id}")
        if result is not None:
            logger.info(f"Cache key {id} found")
            json_result = from_json(result)
            redis_element = RedisCacheElement(duration=json_result["duration"], data=json_result["data"])
            self.redis.expire(
                redis_key,
                redis_element.duration if refresh_timeout is None else refresh_timeout,
            )
            return redis_element.data
        logger.info(f"Cache key {id} not found")
        return None

    @override
    def invalidate(self, id: str) -> None:
        logger.info(f"Removing cache key {id}")
        self.redis.delete(f"cache:{id}")

    @override
    def invalidate_all(self, ids: List[str]) -> None:
        logger.info(f"Removing cache keys {ids}")
        self.redis.delete(*[f"cache:{id}" for id in ids])
