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
import threading
import time
from typing import Dict, List, Optional

from typing_extensions import override

from antarest.core.config import CacheConfig
from antarest.core.interfaces.cache import ICache
from antarest.core.model import JSON
from antarest.core.serde import AntaresBaseModel

logger = logging.getLogger(__name__)


class LocalCacheElement(AntaresBaseModel):
    timeout: int
    duration: int
    data: JSON


class LocalCache(ICache):
    def __init__(self, config: CacheConfig = CacheConfig()):
        self.cache: Dict[str, LocalCacheElement] = {}
        self.lock = threading.Lock()
        self.checker_delay = config.checker_delay
        self.checker_thread = threading.Thread(
            target=self.checker,
            name=self.__class__.__name__,
            daemon=True,
        )

    @override
    def start(self) -> None:
        self.checker_thread.start()

    def checker(self) -> None:
        while True:
            time.sleep(self.checker_delay)
            with self.lock:
                current_time = time.time()
                to_delete: List[str] = []
                for id in self.cache.keys():
                    if current_time >= self.cache[id].timeout:
                        to_delete.append(id)
                for id in to_delete:
                    del self.cache[id]

    @override
    def put(self, id: str, data: JSON, duration: int = 3600) -> None:  # Duration in second
        with self.lock:
            logger.info(f"Adding cache key {id}")
            self.cache[id] = LocalCacheElement(
                data=data,
                timeout=(int(time.time()) + duration),
                duration=duration,
            )

    @override
    def get(self, id: str, refresh_duration: Optional[int] = None) -> Optional[JSON]:
        res = None
        with self.lock:
            logger.info(f"Trying to retrieve cache key {id}")
            if id in self.cache:
                logger.info(f"Cache key {id} found")
                if refresh_duration:
                    self.cache[id].duration = refresh_duration
                self.cache[id].timeout = int(time.time()) + self.cache[id].duration
                res = self.cache[id].data
        return res

    @override
    def invalidate(self, id: str) -> None:
        with self.lock:
            logger.info(f"Removing cache key {id}")
            if id in self.cache:
                del self.cache[id]

    @override
    def invalidate_all(self, ids: List[str]) -> None:
        with self.lock:
            logger.info(f"Removing cache keys {ids}")
            for id in ids:
                if id in self.cache:
                    del self.cache[id]
