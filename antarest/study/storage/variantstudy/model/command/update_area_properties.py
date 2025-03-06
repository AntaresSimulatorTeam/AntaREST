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

from antarest.study.business.model.area_model import AreaPropertiesUpdate, decode_filter
from antarest.study.storage.rawstudy.model.filesystem.config.area import (
    AdequacyPathProperties,
    OptimizationProperties,
    ThermalAreasProperties,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import ICommand, OutputTuple
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


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
        for area_id, properties in self.areas_properties.items():
            self.update_thermal_properties(area_id, study_data)
            self.update_adequacy_patch(area_id, study_data)
            self.update_area_optimization(area_id, study_data)

        output, _ = self._apply_config(study_data.config)

        return output

    def update_thermal_properties(self, area_id: str, study_data: FileStudy) -> None:
        if (new_properties := self.areas_properties[area_id].thermal_properties) != {}:
            thermal_properties = study_data.tree.get(["input", "thermal", "areas"])

            for k, v in new_properties.items():
                thermal_properties[k].update({area_id: v})

            ThermalAreasProperties.model_validate(thermal_properties)

            study_data.tree.save(thermal_properties, ["input", "thermal", "areas"])

    def update_adequacy_patch(self, area_id: str, study_data: FileStudy) -> None:
        if (new_properties := self.areas_properties[area_id].adequacy_patch_property) != {}:
            adequacy_patch_properties = study_data.tree.get(["input", "areas", area_id, "adequacy_patch"])
            adequacy_patch_properties["adequacy-patch"].update(new_properties)

            AdequacyPathProperties.model_validate(adequacy_patch_properties)

            study_data.tree.save(adequacy_patch_properties, ["input", "areas", area_id, "adequacy_patch"])

    def update_area_optimization(self, area_id: str, study_data: FileStudy) -> None:
        new_filtering = self.areas_properties[area_id].filtering_props
        new_nodal = self.areas_properties[area_id].optim_properties

        if new_filtering or new_nodal:
            optimization_properties = study_data.tree.get(["input", "areas", area_id, "optimization"])

            if new_nodal:
                optimization_properties["nodal optimization"].update(new_nodal)

            if new_filtering:
                if synthesis := new_filtering.get("filter-synthesis"):
                    optimization_properties["filtering"]["filter-synthesis"] = decode_filter(synthesis)
                if by_year := new_filtering.get("filter-year-by-year"):
                    optimization_properties["filtering"]["filter-year-by-year"] = decode_filter(by_year)

            OptimizationProperties.model_validate(optimization_properties)

            study_data.tree.save(optimization_properties, ["input", "areas", area_id, "optimization"])

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
