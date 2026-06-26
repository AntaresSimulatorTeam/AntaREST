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
from antarest.study.business.model.reserve_symmetries_model import ReserveSymmetry, merge_symmetries
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


class RemoveThermalReserveSymmetries(ICommand):
    """
    Command used to remove several new thermal reserve symmetries in the study.
    """

    command_name: CommandName = CommandName.REMOVE_THERMAL_RESERVE_SYMMETRIES

    # Command parameters
    # ==================

    area_id: AreaId
    thermal_id: ThermalId
    symmetries: list[ReserveSymmetry]

    @model_validator(mode="after")
    def _validate_version_and_symmetries(self) -> Self:
        if self.study_version < STUDY_VERSION_10_0:
            msg = "Thermal cluster reserve symmetries are not valid for study version before 10.0"
            raise InvalidFieldForVersionError(msg)

        self.symmetries = merge_symmetries(self.symmetries)
        return self

    @override
    def _apply_dao(self, study_data: StudyDao, listener: ICommandListener | None = None) -> CommandOutput[None]:
        existing_symmetries = study_data.get_thermal_reserve_symmetries(self.area_id)
        if self.thermal_id not in existing_symmetries:
            return command_failed(
                f"Thermal cluster '{self.thermal_id}' does not have reserve symmetries in area '{self.area_id}'"
            )

        new_symmetries = []
        for existing_symmetry in existing_symmetries[self.thermal_id]:
            if existing_symmetry not in self.symmetries:
                new_symmetries.append(existing_symmetry)

        if len(new_symmetries) != len(existing_symmetries[self.thermal_id]) - len(self.symmetries):
            return command_failed(
                f"Some thermal cluster reserve symmetry in '{self.symmetries}' does not exist for thermal '{self.thermal_id}' in area '{self.area_id}'"
            )

        study_data.save_thermal_reserve_symmetries({self.area_id: {self.thermal_id: new_symmetries}})

        if not study_data.thermal_exists(self.area_id, self.thermal_id):
            return command_failed(f"Thermal cluster '{self.thermal_id}' does not exist in area '{self.area_id}'")

        study_data.save_thermal_reserve_symmetries({self.area_id: {self.thermal_id: new_symmetries}})

        msg = f"Reserve symmetries from thermal '{self.thermal_id}' in area '{self.area_id}' removed successfully."
        return command_succeeded(msg, result=None)

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.REMOVE_THERMAL_RESERVE_CERTIFICATIONS.value,
            args={"area_id": self.area_id, "thermal_id": self.thermal_id, "symmetries": self.symmetries},
            study_version=self.study_version,
        )
