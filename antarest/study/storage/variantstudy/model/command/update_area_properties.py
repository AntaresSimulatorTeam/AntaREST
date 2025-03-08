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
from typing import Dict, List, Optional

from typing_extensions import override

from antarest.study.business.model.area_properties_model import AreaPropertiesUpdate, AreaPropertiesProperties
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import ICommand, OutputTuple
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


THERMAL_PATH = ["input", "thermal", "areas"]
OPTIMIZATION_PATH = ["input", "areas", "{area_id}", "optimization"]
ADEQUACY_PATCH_PATH = ["input", "areas", "{area_id}", "adequacy_patch", "adequacy-patch"]

class UpdateAreasProperties(ICommand):
    """
    Command used to update multiple areas properties
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_AREAS_PROPERTIES

    # Command parameters
    # ==================
    areas_properties: Dict[str, AreaPropertiesUpdate]

    @override
    def _apply_config(self, study_data: FileStudyTreeConfig) -> OutputTuple:
        updated_areas = ", ".join(self.areas_properties.keys())
        return CommandOutput(status=True, message=f"Areas properties updated: {updated_areas}"), {}

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        for area_id, area_properties in self.areas_properties.items():
            current_thermal_props = study_data.tree.get(THERMAL_PATH)
            current_optim_properties = study_data.tree.get([s.format(area_id=area_id) for s in OPTIMIZATION_PATH])
            current_adequacy_patch = study_data.tree.get([s.format(area_id=area_id) for s in ADEQUACY_PATCH_PATH])

            properties = {
                **current_thermal_props,
                **current_optim_properties.get("nodal optimization", {}),
                **current_optim_properties.get("filtering", {}),
                **current_adequacy_patch
            }

            current_properties = AreaPropertiesProperties(**properties)

            new_properties = current_properties.get_area_properties(area_id=self.area_id).model_copy(
                update=self.properties.model_dump(exclude_none=True)
            )

            current_properties.set_area_properties(self.area_id, new_properties)

        output, _ = self._apply_config(study_data.config)

        return output

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.UPDATE_AREAS_PROPERTIES.value,
            args={
                "areas_properties": self.areas_properties,
            },
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
