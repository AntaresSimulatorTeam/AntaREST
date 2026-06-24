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
from antarest.study.business.model.reserve_definition_model import ReserveDefinitionId
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.dao.common import AreaId, ThermalId
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


class RemoveThermalReserveCertifications(ICommand):
    """
    Command used to remove several new thermal reserve certifications in the study.
    """

    command_name: CommandName = CommandName.REMOVE_THERMAL_RESERVE_CERTIFICATIONS

    # Command parameters
    # ==================

    area_id: AreaId
    thermal_id: ThermalId
    reserve_ids: list[ReserveDefinitionId]

    @model_validator(mode="after")
    def _validate_version(self) -> Self:
        if self.study_version < STUDY_VERSION_10_0:
            msg = "Thermal cluster reserve certifications are not valid for study version before 10.0"
            raise InvalidFieldForVersionError(msg)
        return self

    @override
    def _apply_dao(self, study_data: StudyDao, listener: ICommandListener | None = None) -> CommandOutput[None]:
        if not study_data.thermal_exists(self.area_id, self.thermal_id):
            return command_failed(f"Thermal cluster '{self.thermal_id}' does not exist in area '{self.area_id}'")

        study_data.delete_thermal_reserve_certifications(self.area_id, self.thermal_id, self.reserve_ids)

        msg = f"Reserve certifications from thermal '{self.thermal_id}' in area '{self.area_id}' removed successfully."
        return command_succeeded(msg, result=None)

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.REMOVE_THERMAL_RESERVE_CERTIFICATIONS.value,
            args={"area_id": self.area_id, "thermal_id": self.thermal_id, "reserve_ids": self.reserve_ids},
            study_version=self.study_version,
        )
