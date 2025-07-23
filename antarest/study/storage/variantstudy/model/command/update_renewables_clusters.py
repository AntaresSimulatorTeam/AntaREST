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

from antarest.core.exceptions import RenewableClusterConfigNotFound
from antarest.study.business.model.renewable_cluster_model import RenewableClusterUpdates, update_renewable_cluster
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


class UpdateRenewablesClusters(ICommand):
    """
    Command used to update several renewable clusters
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_RENEWABLES_CLUSTERS

    # Command parameters
    # ==================

    cluster_properties: RenewableClusterUpdates

    @override
    def _apply_dao(self, study_data: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
        """
        We validate ALL objects before saving them.
        This way, if some data is invalid, we're not modifying the study partially only.
        """
        memory_mapping = {}

        for area_id, value in self.cluster_properties.items():
            try:
                all_renewables_per_area = study_data.get_all_renewables_for_area(area_id)
            except RenewableClusterConfigNotFound:
                return command_failed(f"The area '{area_id}' is not found.")

            existing_ids = {renewable.id.lower(): renewable for renewable in all_renewables_per_area}

            new_clusters = []
            for cluster_id, new_properties in value.items():
                if cluster_id not in existing_ids:
                    return command_failed(f"The renewable cluster '{cluster_id}' in the area '{area_id}' is not found.")

                current_cluster = existing_ids[cluster_id]
                new_cluster = update_renewable_cluster(current_cluster, new_properties)
                new_clusters.append(new_cluster)

            memory_mapping[area_id] = new_clusters

        for area_id, new_clusters in memory_mapping.items():
            study_data.save_renewables(area_id, new_clusters)

        return command_succeeded("The renewable clusters were successfully updated.")

    @override
    def to_dto(self) -> CommandDTO:
        args: dict[str, dict[str, Any]] = {}

        for area_id, value in self.cluster_properties.items():
            for cluster_id, properties in value.items():
                args.setdefault(area_id, {})[cluster_id] = properties.model_dump(mode="json", exclude_unset=True)

        return CommandDTO(
            action=self.command_name.value, args={"cluster_properties": args}, study_version=self.study_version
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
