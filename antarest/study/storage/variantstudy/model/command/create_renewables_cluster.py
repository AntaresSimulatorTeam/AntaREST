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

from typing import Any, Dict, Final, List, Optional

from pydantic import ValidationInfo, model_validator
from typing_extensions import override

from antarest.study.business.model.renewable_cluster_model import RenewableClusterCreation, create_renewable_cluster
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.storage.rawstudy.model.filesystem.config.renewable import parse_renewable_cluster
from antarest.study.storage.rawstudy.model.filesystem.config.validation import AreaId
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
    command_failed,
    command_succeeded,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class CreateRenewablesCluster(ICommand):
    """
    Command used to create a renewable cluster in an area.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.CREATE_RENEWABLES_CLUSTER

    # version 2: remove cluster_name and type parameters as RenewableProperties
    _SERIALIZATION_VERSION: Final[int] = 2

    # Command parameters
    # ==================

    area_id: AreaId
    parameters: RenewableClusterCreation

    @model_validator(mode="before")
    @classmethod
    def validate_model(cls, values: Dict[str, Any], info: ValidationInfo) -> Dict[str, Any]:
        # Validate parameters
        if isinstance(values["parameters"], dict):
            parameters = values["parameters"]
            if info.context and info.context.version == 1:
                parameters["name"] = values.pop("cluster_name")
            cluster = parse_renewable_cluster(parameters)
            values["parameters"] = RenewableClusterCreation.from_cluster(cluster)
        return values

    @override
    def _apply_dao(self, study_data: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
        renewable = create_renewable_cluster(self.parameters)
        renewable_id = renewable.get_id()
        lower_renewable_id = renewable_id.lower()
        if study_data.renewable_exists(self.area_id, lower_renewable_id):
            return command_failed(f"Renewable cluster '{renewable_id}' already exists in the area '{self.area_id}'")

        study_data.save_renewable(self.area_id, renewable)

        # Matrices
        null_matrix = self.command_context.generator_matrix_constants.get_null_matrix()
        study_data.save_renewable_series(self.area_id, lower_renewable_id, null_matrix)

        return command_succeeded(f"Renewable cluster '{renewable_id}' added to area '{self.area_id}'.")

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            version=self._SERIALIZATION_VERSION,
            args={
                "area_id": self.area_id,
                "parameters": self.parameters.model_dump(mode="json", by_alias=True, exclude_none=True),
            },
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
