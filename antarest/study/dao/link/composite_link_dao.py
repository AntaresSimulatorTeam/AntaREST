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
from antarest.study.business.model.link_model import LinkBaseDTO, LinkDTO
from antarest.study.dao.link.cache_link_dao import CacheLinkDao
from antarest.study.dao.link.storage_link_dao import StorageLinkDao
from antarest.study.model import Study
from antarest.study.storage.storage_service import StudyStorageService


class CompositeLinkDAO:
    def __init__(self, storage_service: StudyStorageService, cache_service: ICache):
        self.storage_dao = StorageLinkDao(storage_service)
        self.cache_dao = CacheLinkDao(cache_service)

    def create_link(self, study: Study, link: LinkDTO) -> LinkDTO:
        self.cache_dao.invalidate(study.id)
        return self.storage_dao.create_link(study, link)

    def get_links(self, study: Study) -> t.List[LinkDTO]:
        links = self.cache_dao.get_links(study.id)
        if links is not None:
            return links

        links = self.storage_dao.get_links(study)

        for link in links:
            self.cache_dao.put(study.id, link)
        return links

    def update_link(self, study: Study, area_from: str, area_to: str, link_update_dto: LinkBaseDTO) -> LinkDTO:
        self.cache_dao.invalidate(study.id)
        return self.storage_dao.update_link(study, area_from, area_to, link_update_dto)

    def update_links(
        self,
        study: Study,
        update_links_by_ids: t.Mapping[t.Tuple[str, str], LinkBaseDTO],
    ) -> t.Mapping[t.Tuple[str, str], LinkBaseDTO]:
        self.cache_dao.invalidate(study.id)
        return self.storage_dao.update_links(study, update_links_by_ids)

    def delete_link(self, study: Study, area_from: str, area_to: str) -> None:
        self.cache_dao.invalidate(study.id)
        self.storage_dao.delete_link(study, area_from, area_to)
