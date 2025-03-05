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

from antarest.study.business.model.renewable_cluster_model import RenewableClusterUpdate
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.config.renewable import (
    RenewableConfig,
    create_renewable_properties,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import ICommand, OutputTuple
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO

_RENEWABLE_CLUSTER_PATH = "input/renewables/clusters/{area_id}/list/{cluster_id}"


class UpdateRenewableCluster(ICommand):
    """
    Command used to update a renewable cluster in an area.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_RENEWABLE_CLUSTER

    # Command parameters
    # ==================

    area_id: str
    cluster_id: str
    properties: RenewableClusterUpdate

    @override
    def _apply_config(self, study_data: FileStudyTreeConfig) -> OutputTuple:
        for index, renewable in enumerate(study_data.areas[self.area_id].renewables):
            if renewable.id == self.cluster_id:
                values = renewable.model_dump()
                values.update(self.properties.model_dump(exclude_unset=True, exclude_none=True))
                study_data.areas[self.area_id].renewables[index] = RenewableConfig.model_validate(values)
                return (
                    CommandOutput(
                        status=True,
                        message=f"The renewable cluster '{self.cluster_id}' in the area '{self.area_id}' has been updated.",
                    ),
                    {},
                )
        return (
            CommandOutput(
                status=False,
                message=f"The renewable cluster '{self.cluster_id}' in the area '{self.area_id}' is not found.",
            ),
            {},
        )

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        path = _RENEWABLE_CLUSTER_PATH.format(area_id=self.area_id, cluster_id=self.cluster_id).split("/")

        current_renewable_properties = create_renewable_properties(
            study_version=self.study_version, data=study_data.tree.get(path)
        )
        new_renewable_properties = current_renewable_properties.model_copy(
            update=self.properties.model_dump(exclude_unset=True)
        )
        new_properties = new_renewable_properties.model_dump(exclude={"id"}, by_alias=True)

        study_data.tree.save(new_properties, path)

        output, _ = self._apply_config(study_data.config)

        return output

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={
                "area_id": self.area_id,
                "cluster_id": self.cluster_id,
                "properties": self.properties.model_dump(mode="json", exclude_unset=True),
            },
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
