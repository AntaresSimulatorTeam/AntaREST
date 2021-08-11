from pathlib import Path
from unittest import mock
import time
from antarest.core.cache.business.local_chache import (
    LocalCache,
    LocalCacheElement,
)
from antarest.core.config import CacheConfig
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
    Area,
)


@mock.patch("time.time", mock.MagicMock(return_value=12345))
def test_lifecycle():
    cache = LocalCache(CacheConfig())
    config = FileStudyTreeConfig(
        study_path=Path("somepath"),
        path=Path("somepath"),
        study_id="",
        version=-1,
        areas={
            "a1": Area(
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
    cache_element = LocalCacheElement(
        duration=duration, data=config, timeout=timeout
    )

    # PUT
    cache.put(id=id, data=config, duration=duration)
    assert cache.cache[id] == cache_element

    # GET
    assert cache.get(id=id) == config
