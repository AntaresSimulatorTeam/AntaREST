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

from typing_extensions import override

from antarest.study.business.model.hydro_model import (
    InflowStructureFileData,
    InflowStructureUpdate,
    get_inflow_path,
)
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput, command_succeeded
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdateInflowStructure(ICommand):
    """
    Command used to update inflow structure in an area.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_INFLOW_STRUCTURE

    # Command parameters
    # ==================

    area_id: str
    properties: InflowStructureUpdate

    @override
    def _apply_dao(self, study_data: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
        file_study = study_data.get_file_study()
        path = get_inflow_path(self.area_id)

        current_inflow = InflowStructureFileData(**file_study.tree.get(path))

        updated_inflow = current_inflow.model_copy(update=self.properties.model_dump()).model_dump(by_alias=True)

        study_data.save_inflow_structure(updated_inflow, path)

        return command_succeeded(f"Inflow properties in '{self.area_id}' updated.")

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.UPDATE_INFLOW_STRUCTURE.value,
            args={"area_id": self.area_id, "properties": self.properties.model_dump(mode="json")},
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
