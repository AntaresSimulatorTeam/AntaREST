# Copyright (c) 2024, RTE (https://www.rte-france.com)
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
from typing import Optional

from redis import Redis

from antarest.core.cache.business.local_chache import LocalCache
from antarest.core.cache.business.redis_cache import RedisCache
from antarest.core.config import Config
from antarest.core.interfaces.cache import ICache

logger = logging.getLogger(__name__)


def build_cache(config: Config, redis_client: Optional[Redis] = None) -> ICache:  # type: ignore
    cache = RedisCache(redis_client) if redis_client is not None else LocalCache(config=config.cache)
    logger.info("Redis cache" if config.redis is not None else "Local cache")
    cache.start()
    return cache
