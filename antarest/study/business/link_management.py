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

from antarest.core.model import JSON
from antarest.study.business.model.link_model import LinkBaseDTO, LinkDTO
from antarest.study.dao.dao_factory import DAOFactory
from antarest.study.model import RawStudy, Study


class LinkManager:
    def __init__(self, dao_factory: DAOFactory) -> None:
        self.composite_dao = dao_factory.create_link_dao()

    def get_all_links(self, study: Study) -> t.List[LinkDTO]:
        return self.composite_dao.get_links(study)

    def create_link(self, study: Study, link_creation_dto: LinkDTO) -> LinkDTO:
        return self.composite_dao.create_link(study, link_creation_dto)

    def update_link(self, study: RawStudy, area_from: str, area_to: str, link_update_dto: LinkBaseDTO) -> LinkDTO:
        return self.composite_dao.update_link(study, area_from, area_to, link_update_dto)

    def update_links(
        self,
        study: RawStudy,
        update_links_by_ids: t.Mapping[t.Tuple[str, str], LinkBaseDTO],
    ) -> t.Mapping[t.Tuple[str, str], LinkBaseDTO]:
        return self.composite_dao.update_links(study, update_links_by_ids)

    def delete_link(self, study: RawStudy, area1_id: str, area2_id: str) -> None:
        self.composite_dao.delete_link(study, area1_id, area2_id)

    @staticmethod
    def get_table_schema() -> JSON:
        return LinkBaseDTO.model_json_schema()
