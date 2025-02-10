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

from pydantic import Field, ValidationInfo, field_validator
from typing_extensions import override

from antarest.core.model import JSON
from antarest.core.utils.utils import assert_this
from antarest.matrixstore.model import MatrixData
from antarest.study.model import STUDY_VERSION_8_7
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    Area,
    FileStudyTreeConfig,
    transform_name_to_id,
)
from antarest.study.storage.rawstudy.model.filesystem.config.thermal import create_thermal_config
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.utils import strip_matrix_protocol, validate_matrix
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class CreateCluster(ICommand):
    """
    Command used to create a thermal cluster in an area.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.CREATE_THERMAL_CLUSTER
    version: int = 1

    # Command parameters
    # ==================

    area_id: str
    cluster_name: str
    parameters: Dict[str, Any]
    prepro: Optional[List[List[MatrixData]] | str] = Field(None, validate_default=True)
    modulation: Optional[List[List[MatrixData]] | str] = Field(None, validate_default=True)

    @field_validator("cluster_name", mode="before")
    def validate_cluster_name(cls, val: str) -> str:
        valid_name = transform_name_to_id(val, lower=False)
        if valid_name != val:
            raise ValueError("Cluster name must only contains [a-zA-Z0-9],&,-,_,(,) characters")
        return val

    @field_validator("prepro", mode="before")
    def validate_prepro(
        cls,
        v: Optional[List[List[MatrixData]] | str],
        values: Dict[str, Any] | ValidationInfo,
    ) -> Optional[List[List[MatrixData]] | str]:
        new_values = values if isinstance(values, dict) else values.data
        if v is None:
            v = new_values["command_context"].generator_matrix_constants.get_thermal_prepro_data()
            return v
        else:
            return validate_matrix(v, new_values)

    @field_validator("modulation", mode="before")
    def validate_modulation(
        cls,
        v: Optional[List[List[MatrixData]] | str],
        values: Dict[str, Any] | ValidationInfo,
    ) -> Optional[List[List[MatrixData]] | str]:
        new_values = values if isinstance(values, dict) else values.data
        if v is None:
            v = new_values["command_context"].generator_matrix_constants.get_thermal_prepro_modulation()
            return v

        else:
            return validate_matrix(v, new_values)

    @override
    def _apply_config(self, study_data: FileStudyTreeConfig) -> Tuple[CommandOutput, Dict[str, Any]]:
        # Search the Area in the configuration
        if self.area_id not in study_data.areas:
            return (
                CommandOutput(
                    status=False,
                    message=f"Area '{self.area_id}' does not exist in the study configuration.",
                ),
                {},
            )
        area: Area = study_data.areas[self.area_id]

        # Check if the cluster already exists in the area
        version = study_data.version
        cluster = create_thermal_config(version, name=self.cluster_name)
        if any(cl.id == cluster.id for cl in area.thermals):
            return (
                CommandOutput(
                    status=False,
                    message=f"Thermal cluster '{cluster.id}' already exists in the area '{self.area_id}'.",
                ),
                {},
            )

        area.thermals.append(cluster)

        return (
            CommandOutput(
                status=True,
                message=f"Thermal cluster '{cluster.id}' added to area '{self.area_id}'.",
            ),
            {"cluster_id": cluster.id},
        )

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        output, data = self._apply_config(study_data.config)
        if not output.status:
            return output

        # default values
        self.parameters.setdefault("name", self.cluster_name)

        cluster_id = data["cluster_id"]
        config = study_data.tree.get(["input", "thermal", "clusters", self.area_id, "list"])
        config[cluster_id] = self.parameters

        # Series identifiers are in lower case.
        series_id = cluster_id.lower()
        null_matrix = self.command_context.generator_matrix_constants.get_null_matrix()
        new_cluster_data: JSON = {
            "input": {
                "thermal": {
                    "clusters": {self.area_id: {"list": config}},
                    "prepro": {
                        self.area_id: {
                            series_id: {
                                "data": self.prepro,
                                "modulation": self.modulation,
                            }
                        }
                    },
                    "series": {self.area_id: {series_id: {"series": null_matrix}}},
                }
            }
        }
        if study_data.config.version >= STUDY_VERSION_8_7:
            new_cluster_data["input"]["thermal"]["series"][self.area_id][series_id]["CO2Cost"] = null_matrix
            new_cluster_data["input"]["thermal"]["series"][self.area_id][series_id]["fuelCost"] = null_matrix
        study_data.tree.save(new_cluster_data)

        return output

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=self.command_name.value,
            args={
                "area_id": self.area_id,
                "cluster_name": self.cluster_name,
                "parameters": self.parameters,
                "prepro": strip_matrix_protocol(self.prepro),
                "modulation": strip_matrix_protocol(self.modulation),
            },
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        matrices: List[str] = []
        if self.prepro:
            assert_this(isinstance(self.prepro, str))
            matrices.append(strip_matrix_protocol(self.prepro))
        if self.modulation:
            assert_this(isinstance(self.modulation, str))
            matrices.append(strip_matrix_protocol(self.modulation))
        return matrices
