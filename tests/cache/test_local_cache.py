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

import time
from pathlib import Path
from unittest import mock

from antares.study.version import StudyVersion

from antarest.core.cache.business.local_chache import LocalCache, LocalCacheElement
from antarest.core.config import CacheConfig
from antarest.study.storage.rawstudy.model.filesystem.config.model import Area, FileStudyTreeConfigDTO


@mock.patch("time.time", mock.MagicMock(return_value=12345))
def test_lifecycle():
    cache = LocalCache(CacheConfig())
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
    duration = 3600
    timeout = int(time.time()) + duration
    cache_element = LocalCacheElement(duration=duration, data=config.model_dump(mode="json"), timeout=timeout)

    # PUT
    cache.put(id=id, data=config.model_dump(mode="json"), duration=duration)
    assert cache.cache[id] == cache_element

    # GET
    assert cache.get(id=id) == config.model_dump(mode="json")
