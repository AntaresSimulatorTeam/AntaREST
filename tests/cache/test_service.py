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
