# Copyright (c) 2026, RTE (https://www.rte-france.com)
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

from collections.abc import Sequence

from antarest.study.business.model.reserve_definition_model import (
    ReserveDefinition,
    ReserveDefinitionCreation,
    ReserveDefinitionUpdate,
    create_reserve_definition,
    update_reserve_definition,
)
from antarest.study.business.study_interface import StudyInterface
from antarest.study.storage.variantstudy.model.command.create_reserve_definition import CreateReserveDefinition
from antarest.study.storage.variantstudy.model.command.remove_reserve_definition import RemoveReserveDefinition
from antarest.study.storage.variantstudy.model.command.update_reserve_definitions import UpdateReserveDefinitions
from antarest.study.storage.variantstudy.model.command_context import CommandContext


class ReserveDefinitionsManager:
    def __init__(self, command_context: CommandContext) -> None:
        self._command_context = command_context

    def get_reserve_definitions(self, study: StudyInterface, area_id: str) -> Sequence[ReserveDefinition]:
        return study.get_study_dao().get_all_reserve_definitions_for_area(area_id)

    def get_reserve_definition(self, study: StudyInterface, area_id: str, reserve_id: str) -> ReserveDefinition:
        return study.get_study_dao().get_reserve_definition(area_id, reserve_id)

    def create_reserve_definition(
        self, study: StudyInterface, area_id: str, data: ReserveDefinitionCreation
    ) -> ReserveDefinition:
        command = CreateReserveDefinition(
            area_id=area_id,
            parameters=data,
            study_version=study.version,
            command_context=self._command_context,
        )
        study.add_commands([command])
        return create_reserve_definition(data)

    def update_reserve_definition(
        self,
        study: StudyInterface,
        area_id: str,
        reserve_id: str,
        data: ReserveDefinitionUpdate,
    ) -> ReserveDefinition:
        reserve = self.get_reserve_definition(study, area_id, reserve_id)
        updated = update_reserve_definition(reserve, data)

        command = UpdateReserveDefinitions(
            reserve_properties={area_id: {reserve_id: data}},
            study_version=study.version,
            command_context=self._command_context,
        )
        study.add_commands([command])
        return updated

    def delete_reserve_definitions(self, study: StudyInterface, area_id: str, reserve_ids: Sequence[str]) -> None:
        commands = [
            RemoveReserveDefinition(
                area_id=area_id,
                reserve_id=reserve_id,
                study_version=study.version,
                command_context=self._command_context,
            )
            for reserve_id in reserve_ids
        ]
        study.add_commands(commands)
