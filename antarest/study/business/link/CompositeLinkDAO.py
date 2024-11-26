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

from typing import List

from antarest.study.business.link.LinkDAO import LinkDAO
from antarest.study.business.model.link_model import LinkDTO
from antarest.study.model import Study


class CompositeLinkDAO(LinkDAO):
    """
    CompositeLinkDAO acts as a composite data access object (DAO) for managing study links.
    It delegates operations to two underlying DAOs: one for cache and one for persistent storage.
    This class ensures that the cache and storage are kept in sync during operations.

    Attributes:
        cache_dao (LinkDAO): The DAO responsible for managing links in the cache.
        storage_dao (LinkDAO): The DAO responsible for managing links in persistent storage.
    """

    def __init__(self, cache_dao: LinkDAO, storage_dao: LinkDAO):
        """
        Initializes the CompositeLinkDAO with a cache DAO and a storage DAO.

        Args:
            cache_dao (LinkDAO): DAO for managing links in the cache.
            storage_dao (LinkDAO): DAO for managing links in persistent storage.
        """
        self.cache_dao = cache_dao
        self.storage_dao = storage_dao

    def get_all_links(self, study: Study) -> List[LinkDTO]:
        """
        Retrieves all links for a given study.

        This method first tries to retrieve links from the cache. If the cache is empty,
        it fetches the links from the persistent storage, updates the cache with the retrieved links,
        and then returns the list of links.

        Args:
            study (Study): The study for which to retrieve the links.

        Returns:
            List[LinkDTO]: A list of all links associated with the study.
        """
        links = self.cache_dao.get_all_links(study)
        if not links:
            links = self.storage_dao.get_all_links(study)
            for link in links:
                self.cache_dao.create_link(study, link)
        return links

    def create_link(self, study: Study, link_dto: LinkDTO) -> LinkDTO:
        """
        Creates a new link for a given study.

        This method adds the link to both the persistent storage and the cache
        to ensure that they remain consistent.

        Args:
            study (Study): The target study.
            link_dto (LinkDTO): The link to be added.

        Returns:
            LinkDTO: The link that was added.
        """
        self.storage_dao.create_link(study, link_dto)
        self.cache_dao.create_link(study, link_dto)
        return link_dto

    def delete_link(self, study: Study, area1_id: str, area2_id: str) -> None:
        """
        Deletes a specific link for a given study.

        This method removes the link from both the persistent storage and the cache
        to ensure consistency between the two.

        Args:
            study (Study): The study containing the link to be deleted.
            area1_id (str): The ID of the source area of the link.
            area2_id (str): The ID of the target area of the link.
        """
        self.storage_dao.delete_link(study, area1_id, area2_id)
        self.cache_dao.delete_link(study, area1_id, area2_id)
