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

from pathlib import Path
from unittest.mock import Mock

from antares.study.version import StudyVersion

from antarest.core.cache.business.redis_cache import RedisCache, RedisCacheElement
from antarest.core.serde.json import from_json
from antarest.study.storage.rawstudy.model.filesystem.config.model import Area, FileStudyTreeConfigDTO


def test_lifecycle():
    redis_client = Mock()
    cache = RedisCache(redis_client)
    config = FileStudyTreeConfigDTO(
        study_path=Path("somepath"),
        path=Path("somepath"),
        study_id="",
        version=StudyVersion.parse(0),
        areas={
            "a1": Area(
                name="a1",
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
    cache_element = RedisCacheElement(duration=duration, data=config.model_dump(mode="json")).model_dump_json()

    # GET
    redis_client.get.return_value = cache_element
    load = from_json(cache_element)
    assert cache.get(id=id) == load["data"]
    redis_client.expire.assert_called_with(redis_key, duration)
    redis_client.get.assert_called_once_with(redis_key)

    # PUT
    duration = 7200
    cache_element = RedisCacheElement(duration=duration, data=config.model_dump(mode="json")).model_dump_json()
    cache.put(id=id, data=config.model_dump(mode="json"), duration=duration)
    redis_client.set.assert_called_once_with(redis_key, cache_element)
    redis_client.expire.assert_called_with(redis_key, duration)
