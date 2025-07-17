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
    update_hydro_management,
)
from antarest.study.dao.api.study_dao import StudyDao
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
    def _apply_dao(self, study_data: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
        hydro_manager = HydroManagementFileData(**study_data.get_file_study().tree.get(HYDRO_PATH))
        hydro_manager.get_hydro_management(self.area_id, study_data.get_version())

        new_hydro = update_hydro_management(
            hydro_manager.get_hydro_management(self.area_id, study_data.get_version()), self.properties
        )

        hydro_manager.set_hydro_management(self.area_id, new_hydro)

        study_data.save_hydro_management(self.area_id, hydro_manager)

        return command_succeeded(f"Hydro properties in '{self.area_id}' updated.")

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
