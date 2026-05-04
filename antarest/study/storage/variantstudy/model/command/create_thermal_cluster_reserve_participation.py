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
from antarest.study.business.model.thermal_cluster_reserve_participation_model import (
    ThermalClusterReserveParticipation,
    ThermalClusterReserveParticipationCreation,
    create_thermal_cluster_reserve_participation,
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


class CreateThermalClusterReserveParticipation(ICommand):
    """
    Command used to create a new thermal cluster reserve participation inside an area.
    """

    command_name: CommandName = CommandName.CREATE_THERMAL_CLUSTER_RESERVE_PARTICIPATION

    area_id: AreaId
    thermal_id: str
    parameters: ThermalClusterReserveParticipationCreation

    @model_validator(mode="after")
    def _validate_version(self) -> Self:
        if self.study_version < STUDY_VERSION_10_0:
            raise InvalidFieldForVersionError(
                "Thermal cluster reserve participations are not valid for study version before 10.0"
            )
        return self

    @override
    def _apply_dao(
        self, study_data: StudyDao, listener: ICommandListener | None = None
    ) -> CommandOutput[ThermalClusterReserveParticipation]:
        # Defensive checks: surface a clear command_failed message rather than letting a
        # DB FK violation bubble up as a 500.
        if not study_data.thermal_exists(self.area_id, self.thermal_id):
            return command_failed(
                f"Thermal cluster '{self.thermal_id}' does not exist in area '{self.area_id}'"
            )
        participation = create_thermal_cluster_reserve_participation(self.parameters)
        if not study_data.reserve_definition_exists(self.area_id, participation.id):
            return command_failed(
                f"Reserve definition '{participation.id}' does not exist in area '{self.area_id}'"
            )
        if study_data.thermal_cluster_reserve_participation_exists(self.area_id, self.thermal_id, participation.id):
            return command_failed(
                f"Reserve participation '{participation.id}' already exists for thermal cluster "
                f"'{self.thermal_id}' in area '{self.area_id}'"
            )
        study_data.save_thermal_cluster_reserve_participations({self.area_id: {self.thermal_id: [participation]}})
        return command_succeeded(
            f"Reserve participation '{participation.id}' added to thermal cluster "
            f"'{self.thermal_id}' in area '{self.area_id}'.",
            result=participation,
        )

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={
                "area_id": self.area_id,
                "thermal_id": self.thermal_id,
                "parameters": self.parameters.model_dump(mode="json", by_alias=True, exclude_none=True),
            },
            study_version=self.study_version,
        )
