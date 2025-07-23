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

from typing import List, Optional

from pydantic import model_validator
from typing_extensions import override

from antarest.study.business.model.hydro_model import (
    HYDRO_PATH,
    HydroManagementFileData,
    HydroManagementUpdate,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput, command_succeeded
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdateHydroManagement(ICommand):
    """
    Command used to update hydro properties in an area.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_HYDRO_PROPERTIES

    # Command parameters
    # ==================

    area_id: str
    properties: HydroManagementUpdate

    @model_validator(mode="after")
    def validate_properties_against_version(self) -> "UpdateHydroManagement":
        self.properties.validate_model_against_version(self.study_version)
        return self

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        current_hydro = HydroManagementFileData(**study_data.tree.get(HYDRO_PATH))

        new_hydro = current_hydro.get_hydro_management(self.area_id, self.study_version).model_copy(
            update=self.properties.model_dump(exclude_none=True)
        )

        current_hydro.set_hydro_management(self.area_id, new_hydro)

        study_data.tree.save(current_hydro.model_dump(by_alias=True, exclude_none=True), HYDRO_PATH)

        return command_succeeded(message=f"Hydro properties in '{self.area_id}' updated.")

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.UPDATE_HYDRO_PROPERTIES.value,
            args={"area_id": self.area_id, "properties": self.properties.model_dump(mode="json", exclude_none=True)},
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
