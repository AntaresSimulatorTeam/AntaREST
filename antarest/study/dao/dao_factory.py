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

from antarest.core.interfaces.cache import ICache
from antarest.study.dao.link.composite_link_dao import CompositeLinkDAO
from antarest.study.storage.storage_service import StudyStorageService


class DAOFactory:
    def __init__(self, storage_service: StudyStorageService, cache_service: ICache):
        self.storage_service = storage_service
        self.cache_service = cache_service

    def create_link_dao(self) -> CompositeLinkDAO:
        return CompositeLinkDAO(self.storage_service, self.cache_service)
