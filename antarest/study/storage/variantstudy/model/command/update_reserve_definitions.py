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
from typing import Any, Self

from pydantic import model_validator
from typing_extensions import override

from antarest.core.exceptions import InvalidFieldForVersionError
from antarest.study.business.model.reserve_definition_model import (
    ReserveDefinition,
    ReserveDefinitionUpdates,
    update_reserve_definition,
)
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.model import STUDY_VERSION_10_0
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
    command_failed,
    command_succeeded,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdateReserveDefinitions(ICommand):
    """
    Command used to update several reserve definitions at once.
    """

    command_name: CommandName = CommandName.UPDATE_RESERVE_DEFINITIONS

    reserve_properties: ReserveDefinitionUpdates

    @model_validator(mode="after")
    def _validate_version(self) -> Self:
        if self.study_version < STUDY_VERSION_10_0:
            raise InvalidFieldForVersionError("Reserve definitions are not valid for study version before 10.0")
        return self

    @override
    def _apply_dao(
        self, study_data: StudyDao, listener: ICommandListener | None = None
    ) -> CommandOutput[dict[str, list[ReserveDefinition]]]:
        memory_mapping: dict[str, list[ReserveDefinition]] = {}

        for area_id, reserves_by_id in self.reserve_properties.items():
            existing_reserves = study_data.get_all_reserve_definitions_for_area(area_id)
            existing_by_id = {r.id: r for r in existing_reserves}

            new_reserves: list[ReserveDefinition] = []
            for reserve_id, new_properties in reserves_by_id.items():
                if reserve_id not in existing_by_id:
                    return command_failed(f"Reserve definition '{reserve_id}' in area '{area_id}' is not found.")
                new_reserves.append(update_reserve_definition(existing_by_id[reserve_id], new_properties))

            memory_mapping[area_id] = new_reserves

        study_data.save_reserve_definitions(memory_mapping)

        return command_succeeded("All reserve definitions updated", result=memory_mapping)

    @override
    def to_dto(self) -> CommandDTO:
        args: dict[str, dict[str, Any]] = {}
        for area_id, reserves_by_id in self.reserve_properties.items():
            for reserve_id, properties in reserves_by_id.items():
                args.setdefault(area_id, {})[reserve_id] = properties.model_dump(
                    mode="json", by_alias=True, exclude_none=True
                )

        return CommandDTO(
            action=self.command_name.value,
            args={"reserve_properties": args},
            study_version=self.study_version,
        )
