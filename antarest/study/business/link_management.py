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

import typing as t
from typing import Any

from antares.study.version import StudyVersion

from antarest.core.exceptions import LinkNotFound
from antarest.core.model import JSON
from antarest.study.business.model.link_model import LinkBaseDTO, LinkDTO, LinkInternal
from antarest.study.business.utils import execute_or_add_commands
from antarest.study.model import RawStudy, Study
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.storage_service import StudyStorageService
from antarest.study.storage.variantstudy.model.command.create_link import CreateLink
from antarest.study.storage.variantstudy.model.command.remove_link import RemoveLink
from antarest.study.storage.variantstudy.model.command.update_link import UpdateLink


class LinkManager:
    def __init__(self, storage_service: StudyStorageService) -> None:
        self.storage_service = storage_service

    def get_all_links(self, study: Study) -> t.List[LinkDTO]:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        result: t.List[LinkDTO] = []

        for area_id, area in file_study.config.areas.items():
            links_config = file_study.tree.get(["input", "links", area_id, "properties"])

            for link in area.links:
                link_tree_config: t.Dict[str, t.Any] = links_config[link]
                link_tree_config.update({"area1": area_id, "area2": link})

                link_internal = LinkInternal.model_validate(link_tree_config)

                result.append(link_internal.to_dto())

        return result

    def get_link(self, study: RawStudy, link: LinkInternal) -> LinkInternal:
        file_study = self.storage_service.get_storage(study).get_raw(study)

        link_properties = self._get_link_if_exists(file_study, link)

        link_properties.update({"area1": link.area1, "area2": link.area2})

        updated_link = LinkInternal.model_validate(link_properties)

        return updated_link

    def create_link(self, study: Study, link_creation_dto: LinkDTO) -> LinkDTO:
        link = link_creation_dto.to_internal(StudyVersion.parse(study.version))

        storage_service = self.storage_service.get_storage(study)
        file_study = storage_service.get_raw(study)

        command = CreateLink(
            area1=link.area1,
            area2=link.area2,
            parameters=link.model_dump(exclude_none=True),
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
            study_version=file_study.config.version,
        )

        execute_or_add_commands(study, file_study, [command], self.storage_service)

        return link_creation_dto

    def _create_update_link_command(
        self, study: Study, area_from: str, area_to: str, link_update_dto: LinkBaseDTO
    ) -> tuple[UpdateLink, LinkInternal]:

        file_study = self.storage_service.get_storage(study).get_raw(study)
        study_version = file_study.config.version

        link_dto = LinkDTO(area1=area_from, area2=area_to, **link_update_dto.model_dump(exclude_unset=True))
        link = link_dto.to_internal(study_version)

        self._get_link_if_exists(file_study, link)

        command = UpdateLink(
            area1=link.area1,
            area2=link.area2,
            parameters=link.model_dump(
                include=link_update_dto.model_fields_set, exclude={"area1", "area2"}, exclude_none=True
            ),
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
            study_version=study_version,
        )
        return command, link

    def update_link(self, study: RawStudy, area_from: str, area_to: str, link_update_dto: LinkBaseDTO) -> LinkDTO:
        command, link = self._create_update_link_command(study, area_from, area_to, link_update_dto)

        file_study = self.storage_service.get_storage(study).get_raw(study)
        execute_or_add_commands(study, file_study, [command], self.storage_service)

        updated_link = self.get_link(study, link)

        return updated_link.to_dto()

    def update_links(
        self,
        study: RawStudy,
        update_links_by_ids: t.Mapping[t.Tuple[str, str], LinkBaseDTO],
    ) -> t.Mapping[t.Tuple[str, str], LinkBaseDTO]:
        file_study = self.storage_service.get_storage(study).get_raw(study)

        # Build all commands
        commands = []
        for (area1, area2), update_link_dto in update_links_by_ids.items():
            command = self._create_update_link_command(study, area1, area2, update_link_dto)[0]
            commands.append(command)

        execute_or_add_commands(study, file_study, commands, self.storage_service)

        # Builds return
        all_links = self.get_all_links(study)
        new_links_by_ids = {}
        for updated_link in all_links:
            # We only return links that were updated
            area_1 = updated_link.area1
            area_2 = updated_link.area2
            if (area_1, area_2) in update_links_by_ids or (area_2, area_1) in update_links_by_ids:
                new_links_by_ids[(area_1, area_2)] = updated_link

        return new_links_by_ids

    def delete_link(self, study: RawStudy, area1_id: str, area2_id: str) -> None:
        file_study = self.storage_service.get_storage(study).get_raw(study)
        command = RemoveLink(
            area1=area1_id,
            area2=area2_id,
            command_context=self.storage_service.variant_study_service.command_factory.command_context,
            study_version=file_study.config.version,
        )
        execute_or_add_commands(study, file_study, [command], self.storage_service)

    def _get_link_if_exists(self, file_study: FileStudy, link: LinkInternal) -> dict[str, Any]:
        try:
            return file_study.tree.get(["input", "links", link.area1, "properties", link.area2])
        except KeyError:
            raise LinkNotFound(f"The link {link.area1} -> {link.area2} is not present in the study")

    @staticmethod
    def get_table_schema() -> JSON:
        return LinkBaseDTO.model_json_schema()
