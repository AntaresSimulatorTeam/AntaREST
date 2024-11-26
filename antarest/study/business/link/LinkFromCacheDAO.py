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

import json
from typing import List

from antarest.core.interfaces.cache import ICache
from antarest.study.business.link.LinkDAO import LinkDAO
from antarest.study.business.model.link_model import LinkDTO
from antarest.study.model import Study


class LinkFromCacheDAO(LinkDAO):
    """
    LinkFromCacheDAO is responsible for managing study links in the cache.
    It provides methods to retrieve, create, and delete links stored in the cache.

    Attributes:
        redis (ICache): The cache interface used for storing and retrieving links.
    """

    def __init__(self, redis: ICache):
        """
        Initializes the LinkFromCacheDAO with a cache interface.

        Args:
            redis (ICache): The cache interface used for managing links.
        """
        self.redis = redis

    def _get_cache_key(self, study_id: str) -> str:
        """
        Generates a unique key for storing the links of a study.

        Args:
            study_id (str): The ID of the studyy.

        Returns:
            str: A unique cache key for the study.
        """
        return f"study:{study_id}:links"

    def get_all_links(self, study: Study) -> List[LinkDTO]:
        """
        Retrieves all links for a given study from the cache.

        This method first checks if the cache contains any links for the given study.
        If no links are found, it returns an empty list. Otherwise, it deserializes the
        links and converts them into instances of LinkDTO.

        Args:
            study (Study): The study for which to retrieve the links.

        Returns:
            List[LinkDTO]: A list of links associated with the study.
        """
        cache_key = self._get_cache_key(study.id)
        cached_links = self.redis.get(cache_key)
        if not cached_links:
            return []
        links_data = cached_links["links"]
        return [LinkDTO.model_validate(link_data) for link_data in links_data]

    def delete_link(self, study: Study, area1_id: str, area2_id: str) -> None:
        """
        Deletes all links associated with a given study from the cache.

        This method invalidates the cache for the specified study, ensuring
        that any subsequent requests will require fetching fresh data.

        Args:
            study (Study): The target study containing the links to delete.
            area1_id (str): The source area of the link to delete.
            area2_id (str): The target area of the link to delete.
        """
        cache_key = self._get_cache_key(study.id)
        self.redis.invalidate(cache_key)

    def create_link(self, study: Study, link_dto: LinkDTO) -> LinkDTO:
        """
        Adds a new link to the study in the cache.

        This method retrieves the current links from the cache, appends the new link,
        and updates the chache with the modified list. If the cache does not exist
        or is invalid, it initialises a new cache entry.

        Args:
            study (Study): The study to which the link belongs.
            link_dto (LinkDTO): The link to add.

        Returns:
            LinkDTO: The newly added link.
        """
        cache_key = self._get_cache_key(study.id)
        cached_links = self.redis.get(cache_key)

        # Deserialize or initialize
        if isinstance(cached_links, str):  # If it's a JSON string
            try:
                cached_links = json.loads(cached_links)  # Deserialize to a Python dict
            except json.JSONDecodeError:
                cached_links = {"links": []}  # Initialize an empty dictionary
        elif not isinstance(cached_links, dict):  # If not a dict, initialize
            cached_links = {"links": []}

        # Access the list of links in cached_links
        links_data = cached_links.get("links", [])
        if not isinstance(links_data, list):  # Ensure it's a list
            links_data = []

        # Add the new link
        link_data = link_dto.model_dump(by_alias=True, exclude_unset=True)
        links_data.append(link_data)

        # Update the cache
        cached_links["links"] = links_data
        self.redis.put(cache_key, cached_links)

        return link_dto
