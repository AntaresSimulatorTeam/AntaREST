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

import typing as t

from antarest.core.interfaces.cache import ICache
from antarest.study.business.model.link_model import LinkDTO


class CacheLinkDao:
    def __init__(self, cache: ICache):
        self.cache = cache

    def get_links(self, study_id: str) -> t.Optional[t.List[LinkDTO]]:
        cache_key = self._get_cache_key(study_id)
        cached_data = self.cache.get(cache_key)
        if cached_data is None:
            return None
        return [LinkDTO.model_validate(link) for link in cached_data["links"]]

    def put(self, study_id: str, link: LinkDTO, timeout: int = 600000) -> None:
        try:
            cache_key = self._get_cache_key(study_id)
            cached_links = self.cache.get(cache_key)

            if cached_links is None:
                cached_links = {"links": []}

            existing_links = cached_links.get("links", [])

            if isinstance(existing_links, dict):
                existing_links = list(existing_links.values())
            elif not isinstance(existing_links, list):
                existing_links = []

            link_data = link.model_dump()
            existing_links.append(link_data)

            cached_links["links"] = existing_links
            self.cache.put(cache_key, cached_links, timeout)
        except:
            raise

    def invalidate(self, study_id: str) -> None:
        cache_key = self._get_cache_key(study_id)
        self.cache.invalidate(cache_key)

    def _get_cache_key(self, study_id: str) -> str:
        return f"links:{study_id}"
