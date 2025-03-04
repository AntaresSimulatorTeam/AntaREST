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

from typing import Any, List, Mapping, Tuple

from antarest.core.exceptions import LinkNotFound
from antarest.core.model import JSON
from antarest.study.business.model.link_model import LinkBaseDTO, LinkDTO, LinkInternal
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.create_link import CreateLink
from antarest.study.storage.variantstudy.model.command.remove_link import RemoveLink
from antarest.study.storage.variantstudy.model.command.update_link import UpdateLink
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class LinkManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_all_links(self, study: StudyInterface) -> List[LinkDTO]:
        return list(study.get_study_dao().get_links())

    def get_link(self, study: StudyInterface, link: LinkInternal) -> LinkDTO:
        return study.get_study_dao().get_link(link.area1, link.area2)

    def create_link(self, study: StudyInterface, link_creation_dto: LinkDTO) -> LinkDTO:
        link = link_creation_dto.to_internal(study.version)

        command = CreateLink(
            area1=link.area1,
            area2=link.area2,
            parameters=link.model_dump(exclude_none=True),
            command_context=self._command_context,
            study_version=study.version,
        )

        study.add_commands([command])

        return link_creation_dto

    def update_link(
        self,
        study: StudyInterface,
        area_from: str,
        area_to: str,
        link_update_dto: LinkBaseDTO,
    ) -> LinkDTO:
        link_dto = LinkDTO(
            area1=area_from,
            area2=area_to,
            **link_update_dto.model_dump(exclude_unset=True),
        )

        file_study = study.get_files()
        link = link_dto.to_internal(study.version)

        self._get_link_if_exists(file_study, link)

        command = UpdateLink(
            area1=link.area1,
            area2=link.area2,
            parameters=link.model_dump(
                include=link_update_dto.model_fields_set,
                exclude={"area1", "area2"},
                exclude_none=True,
            ),
            command_context=self._command_context,
            study_version=study.version,
        )

        study.add_commands([command])
        return self.get_link(study, link)

    def update_links(
        self,
        study: StudyInterface,
        update_links_by_ids: Mapping[Tuple[str, str], LinkBaseDTO],
    ) -> Mapping[Tuple[str, str], LinkBaseDTO]:
        new_links_by_ids = {}
        for (area1, area2), update_link_dto in update_links_by_ids.items():
            updated_link = self.update_link(study, area1, area2, update_link_dto)
            new_links_by_ids[(area1, area2)] = updated_link

        return new_links_by_ids

    def delete_link(self, study: StudyInterface, area1_id: str, area2_id: str) -> None:
        command = RemoveLink(
            area1=area1_id,
            area2=area2_id,
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])

    def _get_link_if_exists(self, file_study: FileStudy, link: LinkInternal) -> dict[str, Any]:
        try:
            return file_study.tree.get(["input", "links", link.area1, "properties", link.area2])
        except KeyError:
            raise LinkNotFound(f"The link {link.area1} -> {link.area2} is not present in the study")

    @staticmethod
    def get_table_schema() -> JSON:
        return LinkBaseDTO.model_json_schema()
