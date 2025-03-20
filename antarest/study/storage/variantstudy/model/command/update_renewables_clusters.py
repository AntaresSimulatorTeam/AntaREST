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
from antarest.study.business.model.renewable_cluster_model import RenewableClusterUpdates
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.config.renewable import (
    RenewableConfig,
    RenewablePropertiesType,
    create_renewable_properties,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import ICommand, OutputTuple
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
    def _apply_config(self, study_data: FileStudyTreeConfig) -> OutputTuple:
        for area_id, value in self.cluster_properties.items():
            if area_id not in study_data.areas:
                return CommandOutput(status=False, message=f"The area '{area_id}' is not found."), {}

            renewable_mapping: dict[str, tuple[int, RenewableConfig]] = {}
            for index, renewable in enumerate(study_data.areas[area_id].renewables):
                renewable_mapping[transform_name_to_id(renewable.id)] = (index, renewable)

            for cluster_id in value:
                if cluster_id not in renewable_mapping:
                    return (
                        CommandOutput(
                            status=False,
                            message=f"The renewable cluster '{cluster_id}' in the area '{area_id}' is not found.",
                        ),
                        {},
                    )
                index, renewable = renewable_mapping[cluster_id]
                current_properties = renewable.model_dump(mode="json")
                current_properties.update(
                    self.cluster_properties[area_id][cluster_id].model_dump(
                        mode="json", exclude_unset=True, exclude_none=True
                    )
                )
                study_data.areas[area_id].renewables[index] = RenewableConfig.model_validate(current_properties)

        return CommandOutput(status=True, message="The renewable clusters were successfully updated."), {}

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        for area_id, value in self.cluster_properties.items():
            ini_path = ["input", "renewables", "clusters", area_id, "list"]

            try:
                all_clusters_for_area = study_data.tree.get(ini_path)
            except ChildNotFoundError:
                return CommandOutput(status=False, message=f"The area '{area_id}' is not found.")

            # Validates the Ini file
            clusters_by_id: dict[str, tuple[str, RenewablePropertiesType]] = {
                transform_name_to_id(k): (k, create_renewable_properties(self.study_version, v))
                for k, v in all_clusters_for_area.items()
            }

            for cluster_id, properties in value.items():
                if cluster_id not in clusters_by_id:
                    return CommandOutput(
                        status=False,
                        message=f"The renewable cluster '{cluster_id}' in the area '{area_id}' is not found.",
                    )
                # Performs the update
                new_properties_dict = properties.model_dump(mode="json", by_alias=False, exclude_unset=True)
                current_properties_obj = clusters_by_id[cluster_id][1]
                updated_obj = current_properties_obj.model_copy(update=new_properties_dict)
                all_clusters_for_area[clusters_by_id[cluster_id][0]] = updated_obj.model_dump(
                    mode="json", by_alias=True
                )

            study_data.tree.save(data=all_clusters_for_area, url=ini_path)

        output, _ = self._apply_config(study_data.config)

        return output

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
