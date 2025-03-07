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

from antarest.study.business.model.inflow_model import INFLOW_PATH, InflowProperties, InflowPropertiesInternal
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import ICommand, OutputTuple
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdateInflowProperties(ICommand):
    """
    Command used to update hydro properties in an area.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_INFLOW_PROPERTIES

    # Command parameters
    # ==================

    area_id: str
    properties: InflowProperties

    @override
    def _apply_config(self, study_data: FileStudyTreeConfig) -> OutputTuple:
        return CommandOutput(status=True, message=f"Inflow properties in '{self.area_id}' updated."), {}

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        path = [s.format(area_id=self.area_id) for s in INFLOW_PATH]

        new_inflow = self.properties.model_dump(exclude_unset=True)
        current_inflow = study_data.tree.get(path)

        new_inflow = InflowPropertiesInternal(**new_inflow).model_dump(by_alias=True, exclude_unset=True)

        current_inflow.update(new_inflow)

        study_data.tree.save(current_inflow, path)

        output, _ = self._apply_config(study_data.config)

        return output

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.UPDATE_INFLOW_PROPERTIES.value,
            args={"area_id": self.area_id, "properties": self.properties.model_dump(mode="json")},
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
