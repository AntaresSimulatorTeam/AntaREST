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
from typing import Self

from pydantic import model_validator
from typing_extensions import override

from antarest.core.exceptions import InvalidFieldForVersionError
from antarest.study.business.model.reserve_definition_model import (
    ReserveDefinition,
    ReserveDefinitionCreation,
    create_reserve_definition,
)
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.model import STUDY_VERSION_10_0
from antarest.study.storage.rawstudy.model.filesystem.config.validation import AreaId
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
    command_failed,
    command_succeeded,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class CreateReserveDefinition(ICommand):
    """
    Command used to create a new reserve definition inside an area.
    """

    command_name: CommandName = CommandName.CREATE_RESERVE_DEFINITION

    area_id: AreaId
    parameters: ReserveDefinitionCreation

    @model_validator(mode="after")
    def _validate_version(self) -> Self:
        if self.study_version < STUDY_VERSION_10_0:
            raise InvalidFieldForVersionError("Reserve definitions are not valid for study version before 10.0")
        return self

    @override
    def _apply_dao(
        self, study_data: StudyDao, listener: ICommandListener | None = None
    ) -> CommandOutput[ReserveDefinition]:
        reserve = create_reserve_definition(self.parameters)
        if study_data.reserve_definition_exists(self.area_id, reserve.id):
            return command_failed(f"Reserve definition '{reserve.id}' already exists in area '{self.area_id}'")

        study_data.save_reserve_definitions({self.area_id: [reserve]})

        return command_succeeded(
            f"Reserve definition '{reserve.id}' added to area '{self.area_id}'.",
            result=reserve,
        )

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={
                "area_id": self.area_id,
                "parameters": self.parameters.model_dump(mode="json", by_alias=True, exclude_none=True),
            },
            study_version=self.study_version,
        )
