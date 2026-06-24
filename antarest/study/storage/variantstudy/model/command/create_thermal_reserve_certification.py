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


from antarest.core.exceptions import InvalidFieldForVersionError
from antarest.study.business.model.reserve_definition_model import ReserveDefinitionId
from antarest.study.business.model.thermal_reserve_certification_model import (
    ThermalReserveCertification,
    ThermalReserveCertificationCreation,
    create_thermal_reserve_certification,
)
from antarest.study.dao.common import AreaId, ThermalId

from typing import Self

from pydantic import model_validator
from typing_extensions import override

from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.model import (
    STUDY_VERSION_10_0,
)
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
    command_failed,
    command_succeeded,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class CreateThermalReserveCertification(ICommand):
    """
    Command used to create a new thermal reserve certification in the study.
    """
    command_name: CommandName = CommandName.CREATE_THERMAL_RESERVE_CERTIFICATION

    # Command parameters
    # ==================

    area_id: AreaId
    thermal_id: ThermalId
    reserve_id: ReserveDefinitionId
    parameters: ThermalReserveCertificationCreation

    @model_validator(mode="after")
    def _validate_version(self) -> Self:
        if self.study_version < STUDY_VERSION_10_0:
            msg = "Thermal cluster reserve certifications are not valid for study version before 10.0"
            raise InvalidFieldForVersionError(msg)
        return self

    @override
    def _apply_dao(self, study_data: StudyDao, listener: ICommandListener | None = None) -> CommandOutput[ThermalReserveCertification]:
        # Performs checks to raise a clear error message if something is wrong
        if not study_data.thermal_exists(self.area_id, self.thermal_id):
            return command_failed(f"Thermal cluster '{self.thermal_id}' does not exist in area '{self.area_id}'")

        if not study_data.reserve_definition_exists(self.area_id, self.reserve_id):
            return command_failed(f"Reserve definition '{self.reserve_id}' does not exist in area '{self.area_id}'")

        if study_data.thermal_reserve_certification_exists(self.area_id, self.thermal_id, self.reserve_id):
            return command_failed(f"Reserve '{self.reserve_id}' already exist for area '{self.area_id}' and thermal '{self.thermal_id}'")

        # Save the data
        certification = create_thermal_reserve_certification(self.parameters)
        study_data.save_thermal_reserve_certifications({self.area_id: {self.thermal_id: {self.reserve_id: certification}}})
        msg = f"Reserve certification '{self.reserve_id}' added to thermal '{self.thermal_id}' in area '{self.area_id}'."
        return command_succeeded(msg, result=certification)

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.CREATE_AREA.value,
            args={
                "area_id": self.area_id,
                "thermal_id": self.thermal_id,
                "reserve_id": self.reserve_id,
                "parameters": self.parameters.model_dump(mode="json")
            },
            study_version=self.study_version,
        )
