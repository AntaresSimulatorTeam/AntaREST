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
from typing import Any, List, Optional

from typing_extensions import override

from antarest.core.exceptions import ChildNotFoundError
from antarest.study.business.model.thermal_model import (
    ThermalCluster,
    ThermalClusterUpdate,
    parse_thermal_cluster,
    serialize_thermal_cluster,
    update_thermal_cluster,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.config.validation import AreaId
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import ICommand, OutputTuple
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO

ClusterID = str
ThermalClusterUpdates = dict[AreaId, dict[ClusterID, ThermalClusterUpdate]]


class UpdateThermalClusters(ICommand):
    """
    Command used to update several thermal clusters
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_THERMAL_CLUSTERS

    # Command parameters
    # ==================

    cluster_properties: ThermalClusterUpdates

    @override
    def _apply_config(self, study_data: FileStudyTreeConfig) -> OutputTuple:
        for area_id, value in self.cluster_properties.items():
            if area_id not in study_data.areas:
                return CommandOutput(status=False, message=f"The area '{area_id}' is not found."), {}

            thermal_mapping: dict[str, tuple[int, ThermalCluster]] = {}
            for index, thermal in enumerate(study_data.areas[area_id].thermals):
                thermal_mapping[thermal.id] = (index, thermal)

            for cluster_id, update in value.items():
                if cluster_id not in thermal_mapping:
                    return (
                        CommandOutput(
                            status=False,
                            message=f"The thermal cluster '{cluster_id}' in the area '{area_id}' is not found.",
                        ),
                        {},
                    )
                index, thermal = thermal_mapping[cluster_id]
                study_data.areas[area_id].thermals[index] = update_thermal_cluster(thermal, update)

        return CommandOutput(status=True, message="The thermal clusters were successfully updated."), {}

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        for area_id, value in self.cluster_properties.items():
            ini_path = ["input", "thermal", "clusters", area_id, "list"]

            try:
                all_clusters_for_area = study_data.tree.get(ini_path)
            except ChildNotFoundError:
                return CommandOutput(status=False, message=f"The area '{area_id}' is not found.")

            for cluster_id, update in value.items():
                if cluster_id not in all_clusters_for_area:
                    return CommandOutput(
                        status=False,
                        message=f"The thermal cluster '{cluster_id}' in the area '{area_id}' is not found.",
                    )

                # Performs the update
                cluster = parse_thermal_cluster(study_data.config.version, all_clusters_for_area[cluster_id])
                updated_cluster = update_thermal_cluster(cluster, update)
                all_clusters_for_area[cluster_id] = serialize_thermal_cluster(
                    study_data.config.version, updated_cluster
                )

            study_data.tree.save(data=all_clusters_for_area, url=ini_path)

        output, _ = self._apply_config(study_data.config)

        return output

    @override
    def to_dto(self) -> CommandDTO:
        args: dict[str, dict[str, Any]] = {}

        for area_id, value in self.cluster_properties.items():
            for cluster_id, properties in value.items():
                args.setdefault(area_id, {})[cluster_id] = properties.model_dump(mode="json", exclude_none=True)

        return CommandDTO(
            action=self.command_name.value, args={"cluster_properties": args}, study_version=self.study_version
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
