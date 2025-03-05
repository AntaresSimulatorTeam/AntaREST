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

from antarest.study.business.model.thermal_cluster_model import ThermalClusterUpdate
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.config.thermal import (
    ThermalConfigType,
    create_thermal_config,
    create_thermal_properties,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import ICommand, OutputTuple
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO

_THERMAL_CLUSTER_PATH = "input/thermal/clusters/{area_id}/list/{thermal_cluster_id}"


class UpdateThermalCluster(ICommand):
    """
    Command used to update a short-term storage in an area.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_THERMAL_CLUSTER

    # Command parameters
    # ==================

    area_id: str
    thermal_cluster_id: str
    properties: ThermalClusterUpdate

    @override
    def _apply_config(self, study_data: FileStudyTreeConfig) -> OutputTuple:
        for index, thermal in enumerate(study_data.areas[self.area_id].thermals):
            if thermal.id == self.thermal_cluster_id:
                thermal_cluster_config = self.update_thermal_config(thermal)
                study_data.areas[self.area_id].thermals[index] = thermal_cluster_config
                return (
                    CommandOutput(
                        status=True,
                        message=f"The thermal cluster '{self.thermal_cluster_id}' in the area '{self.area_id}' has been updated.",
                    ),
                    {},
                )
        return (
            CommandOutput(
                status=False,
                message=f"The thermal cluster '{self.thermal_cluster_id}' in the area '{self.area_id}' is not found.",
            ),
            {},
        )

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        path = _THERMAL_CLUSTER_PATH.format(area_id=self.area_id, thermal_cluster_id=self.thermal_cluster_id).split("/")

        current_thermal_properties = create_thermal_properties(
            study_version=self.study_version, data=study_data.tree.get(path)
        )
        new_thermal_properties = current_thermal_properties.model_copy(
            update=self.properties.model_dump(exclude_unset=True)
        )
        new_properties = new_thermal_properties.model_dump(by_alias=True)

        study_data.tree.save(new_properties, path)

        output, _ = self._apply_config(study_data.config)

        return output

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={
                "area_id": self.area_id,
                "thermal_cluster_id": self.thermal_cluster_id,
                "properties": self.properties.model_dump(mode="json", exclude_unset=True),
            },
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []

    def update_thermal_config(self, thermal: ThermalConfigType) -> ThermalConfigType:
        # Set the object to the correct version
        versioned_thermal = create_thermal_config(
            study_version=self.study_version, **thermal.model_dump(exclude_unset=True, exclude_none=True)
        )
        # Update the object with the new properties
        updated_versioned_thermal = versioned_thermal.model_copy(
            update=self.properties.model_dump(exclude_unset=True, exclude_none=True)
        )
        # Create the new object to be saved
        thermal_cluster_config = create_thermal_config(
            study_version=self.study_version,
            **updated_versioned_thermal.model_dump(),
        )
        return thermal_cluster_config
