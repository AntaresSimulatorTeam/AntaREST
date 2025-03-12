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
from typing import Any, Dict, List, Optional, Tuple

from typing_extensions import override

from antarest.study.business.model.area_properties_model import (
    AreaPropertiesProperties,
    AreaPropertiesUpdate,
    get_adequacy_patch_path,
    get_optimization_path,
    get_thermal_path,
)
from antarest.study.model import STUDY_VERSION_8_3
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
    properties: Dict[str, AreaPropertiesUpdate]

    @override
    def _apply_config(self, study_data: FileStudyTreeConfig) -> OutputTuple:
        updated_areas = ", ".join(self.properties.keys())
        return CommandOutput(status=True, message=f"Areas properties updated: {updated_areas}"), {}

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        current_properties: AreaPropertiesProperties = AreaPropertiesProperties(
            thermal_properties=ThermalAreasProperties(),
            optimization_properties=OptimizationProperties(),
            adequacy_properties=AdequacyPathProperties(),
        )

        current_thermal_props = ThermalAreasProperties(**study_data.tree.get(get_thermal_path()))

        for area_id, area_properties in self.properties.items():
            current_optim_properties, current_adequacy_patch = self.fetch_area_properties(study_data, area_id)

            current_properties = AreaPropertiesProperties(
                thermal_properties=current_thermal_props,
                optimization_properties=OptimizationProperties(**current_optim_properties),
                adequacy_properties=AdequacyPathProperties(**current_adequacy_patch),
            )

            new_properties = current_properties.get_area_properties(area_id=area_id).model_copy(
                update=area_properties.model_dump(exclude_none=True)
            )

            current_properties.set_area_properties(area_id, new_properties)

            current_thermal_props = current_properties.thermal_properties

            self.save_area_properties(study_data, area_id, current_properties)

        study_data.tree.save(current_properties.thermal_properties.model_dump(by_alias=True), get_thermal_path())

        output, _ = self._apply_config(study_data.config)

        return output

    def save_area_properties(
        self, study_data: FileStudy, area_id: str, current_properties: AreaPropertiesProperties
    ) -> None:
        study_data.tree.save(
            current_properties.optimization_properties.model_dump(by_alias=True),
            get_optimization_path(area_id),
        )
        if self.study_version >= STUDY_VERSION_8_3:
            study_data.tree.save(
                current_properties.adequacy_properties.model_dump(),
                get_adequacy_patch_path(area_id),
            )

    def fetch_area_properties(self, study_data: FileStudy, area_id: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        current_optim_properties = study_data.tree.get(get_optimization_path(area_id))
        current_adequacy_patch = (
            study_data.tree.get(get_adequacy_patch_path(area_id)) if self.study_version >= STUDY_VERSION_8_3 else {}
        )

        return current_optim_properties, current_adequacy_patch

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.UPDATE_AREAS_PROPERTIES.value,
            args={
                "properties": {
                    area_id: props.model_dump(mode="json", exclude_none=True)
                    for area_id, props in self.properties.items()
                },
            },
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
