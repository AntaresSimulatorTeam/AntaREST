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

from abc import abstractmethod
from enum import Enum
from typing import List, Optional

from antarest.core.model import JSON


class CacheConstants(Enum):
    """
    Constants used to identify cache entries.

    - `RAW_STUDY`: variable used to store JSON (or bytes) objects.
      This cache is used by the `RawStudyService` or `VariantStudyService` to store
      values that are retrieved from the filesystem.
      Note: that it is unlikely that this cache is used, because it is only used
      to fetch data inside a study when the URL is "" and the depth is -1.

    - `STUDY_FACTORY`: variable used to store objects of type `FileStudyTreeConfigDTO`.
      This cache is used by the `create_from_fs` function when retrieving the configuration
      of a study from the data on the disk.

    """

    RAW_STUDY = "RAW_STUDY"
    STUDY_FACTORY = "STUDY_FACTORY"


def study_config_cache_key(study_id: str) -> str:
    """
    The key of study config object in cache
    """
    return f"{CacheConstants.STUDY_FACTORY}/{study_id}"


class ICache:
    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def put(self, id: str, data: JSON, timeout: int = 600000) -> None:
        pass

    @abstractmethod
    def get(self, id: str, refresh_timeout: Optional[int] = None) -> Optional[JSON]:
        pass

    @abstractmethod
    def invalidate(self, id: str) -> None:
        pass

    @abstractmethod
    def invalidate_all(self, ids: List[str]) -> None:
        pass
