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
from typing import Any, List, Optional, Self

from pydantic import model_validator
from typing_extensions import override

from antarest.study.business.model.thermal_cluster_model import (
    ThermalClusterUpdates,
    update_thermal_cluster,
    validate_thermal_cluster_against_version,
)
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
    command_failed,
    command_succeeded,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


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

    @model_validator(mode="after")
    def _validate_against_version(self) -> Self:
        for clusters in self.cluster_properties.values():
            for cluster in clusters.values():
                validate_thermal_cluster_against_version(self.study_version, cluster)
        return self

    @override
    def _apply_dao(self, study_data: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
        """
        We validate ALL objects before saving them.
        This way, if some data is invalid, we're not modifying the study partially only.
        """
        memory_mapping = {}

        all_thermals = study_data.get_all_thermals()

        for area_id, value in self.cluster_properties.items():
            if area_id not in all_thermals:
                return command_failed(f"Area '{area_id}' does not exist")

            new_clusters = []
            for cluster_id, new_properties in value.items():
                lowered_id = cluster_id.lower()
                if lowered_id not in all_thermals[area_id]:
                    return command_failed(f"The thermal cluster '{cluster_id}' in the area '{area_id}' is not found.")

                current_cluster = all_thermals[area_id][lowered_id]
                new_cluster = update_thermal_cluster(current_cluster, new_properties)
                new_clusters.append(new_cluster)

            memory_mapping[area_id] = new_clusters

        for area_id, new_clusters in memory_mapping.items():
            study_data.save_thermals(area_id, new_clusters)

        return command_succeeded("All thermal clusters updated")

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
