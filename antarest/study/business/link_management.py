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

from typing import List, Mapping, Tuple

from antarest.core.model import JSON
from antarest.study.business.model.link_model import Link, LinkUpdate
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.rawstudy.model.filesystem.config.link import serialize_link
from antarest.study.storage.variantstudy.model.command.create_link import CreateLink
from antarest.study.storage.variantstudy.model.command.remove_link import RemoveLink
from antarest.study.storage.variantstudy.model.command.update_link import UpdateLink
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class LinkManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_all_links(self, study: StudyInterface) -> List[Link]:
        return list(study.get_study_dao().get_links())

    def get_link(self, study: StudyInterface, area_from: str, area_to: str) -> Link:
        return study.get_study_dao().get_link(area_from, area_to)

    def create_link(self, study: StudyInterface, new_link: Link) -> Link:
        command = CreateLink(
            area1=new_link.area1,
            area2=new_link.area2,
            parameters=serialize_link(study.version, new_link),
            command_context=self._command_context,
            study_version=study.version,
        )

        study.add_commands([command])

        return new_link

    def _create_update_link_command(
        self, study: StudyInterface, area_from: str, area_to: str, link_update_dto: LinkUpdate
    ) -> UpdateLink:
        self.get_link(study, area_from, area_to)

        command = UpdateLink(
            area1=area_from,
            area2=area_to,
            parameters=link_update_dto.model_dump(exclude_none=True),
            command_context=self._command_context,
            study_version=study.version,
        )
        return command

    def update_link(self, study: StudyInterface, area_from: str, area_to: str, link_update_dto: LinkUpdate) -> Link:
        command = self._create_update_link_command(study, area_from, area_to, link_update_dto)

        study.add_commands([command])
        return self.get_link(study, area_from, area_to)

    def update_links(
        self,
        study: StudyInterface,
        update_links_by_ids: Mapping[Tuple[str, str], LinkUpdate],
    ) -> Mapping[Tuple[str, str], Link]:
        # Build all commands
        commands = []
        for (area1, area2), update_link_dto in update_links_by_ids.items():
            command = self._create_update_link_command(study, area1, area2, update_link_dto)
            commands.append(command)

        study.add_commands(commands)

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

    def delete_link(self, study: StudyInterface, area1_id: str, area2_id: str) -> None:
        command = RemoveLink(
            area1=area1_id,
            area2=area2_id,
            command_context=self._command_context,
            study_version=study.version,
        )
        study.add_commands([command])

    @staticmethod
    def get_table_schema() -> JSON:
        return LinkUpdate.model_json_schema()
