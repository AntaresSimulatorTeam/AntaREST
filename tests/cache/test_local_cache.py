import time
from pathlib import Path
from unittest import mock

from antarest.core.cache.business.local_chache import (
    LocalCache,
    LocalCacheElement,
)
from antarest.core.config import CacheConfig
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
    Area,
    FileStudyTreeConfigDTO,
)


@mock.patch("time.time", mock.MagicMock(return_value=12345))
def test_lifecycle():
    cache = LocalCache(CacheConfig())
    config = FileStudyTreeConfigDTO(
        study_path=Path("somepath"),
        path=Path("somepath"),
        study_id="",
        version=-1,
        areas={
            "a1": Area(
                name="a1",
                links={},
                thermals=[],
                renewables=[],
                filters_synthesis=[],
                filters_year=[],
                st_storage=[],
            )
        },
    )
    id = "some_id"
    duration = 3600
    timeout = int(time.time()) + duration
    cache_element = LocalCacheElement(
        duration=duration, data=config.dict(), timeout=timeout
    )

    # PUT
    cache.put(id=id, data=config.dict(), duration=duration)
    assert cache.cache[id] == cache_element

    # GET
    assert cache.get(id=id) == config.dict()
