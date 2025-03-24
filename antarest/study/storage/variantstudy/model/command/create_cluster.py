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
import typing as t
from typing import Any, Dict, Final, List, Optional, Tuple

from antares.study.version import StudyVersion
from pydantic import Field, model_validator
from pydantic_core.core_schema import ValidationInfo
from typing_extensions import override

from antarest.core.model import JSON
from antarest.core.utils.utils import assert_this
from antarest.matrixstore.model import MatrixData
from antarest.study.business.model.thermal_model import (
    ThermalCluster,
    ThermalClusterCreation,
    parse_thermal_cluster,
    serialize_thermal_cluster,
)
from antarest.study.model import STUDY_VERSION_8_7
from antarest.study.storage.rawstudy.model.filesystem.config.model import Area, FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.config.validation import AreaId
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.utils import strip_matrix_protocol, validate_matrix
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO

OptionalMatrixData: t.TypeAlias = List[List[MatrixData]] | str | None


def _to_cluster(cluster_creation: ThermalClusterCreation) -> ThermalCluster:
    return ThermalCluster.model_validate(cluster_creation.model_dump(exclude_none=True))


class CreateCluster(ICommand):
    """
    Command used to create a thermal cluster in an area.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.CREATE_THERMAL_CLUSTER

    # Command parameters
    # ==================

    area_id: AreaId
    parameters: ThermalClusterCreation
    prepro: OptionalMatrixData = Field(None, validate_default=True)
    modulation: OptionalMatrixData = Field(None, validate_default=True)

    # version 2: remove cluster_name and type parameters as ThermalPropertiesType
    # version 3: type parameters as ThermalClusterCreation
    _SERIALIZATION_VERSION: Final[int] = 3

    @property
    def cluster_name(self) -> str:
        return self.parameters.name

    @model_validator(mode="before")
    @classmethod
    def validate_model(cls, values: Dict[str, t.Any], info: ValidationInfo) -> Dict[str, Any]:
        # Validate parameters
        if isinstance(values["parameters"], dict):
            study_version = StudyVersion.parse(values["study_version"])
            parameters = values["parameters"]
            if info.context:
                version = info.context.version
                if version == 1:
                    parameters["name"] = values.pop("cluster_name")
                if version < 3:
                    cluster = parse_thermal_cluster(study_version, parameters)
                    values["parameters"] = ThermalClusterCreation.from_cluster(cluster)

        # Validate prepro
        if "prepro" in values:
            values["prepro"] = validate_matrix(values["prepro"], values)
        else:
            values["prepro"] = values["command_context"].generator_matrix_constants.get_thermal_prepro_data()

        # Validate modulation
        if "modulation" in values:
            values["modulation"] = validate_matrix(values["modulation"], values)
        else:
            values["modulation"] = values["command_context"].generator_matrix_constants.get_thermal_prepro_modulation()

        return values

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
        cluster = ThermalCluster.model_validate({"name": self.cluster_name})
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

        version = study_data.config.version

        cluster_id = data["cluster_id"]
        config = study_data.tree.get(["input", "thermal", "clusters", self.area_id, "list"])
        cluster = _to_cluster(self.parameters)
        config[cluster_id] = serialize_thermal_cluster(study_data.config.version, cluster)

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
        if version >= STUDY_VERSION_8_7:
            new_cluster_data["input"]["thermal"]["series"][self.area_id][series_id]["CO2Cost"] = null_matrix
            new_cluster_data["input"]["thermal"]["series"][self.area_id][series_id]["fuelCost"] = null_matrix
        study_data.tree.save(new_cluster_data)

        return output

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            version=self._SERIALIZATION_VERSION,
            action=self.command_name.value,
            args={
                "area_id": self.area_id,
                "parameters": self.parameters.model_dump(mode="json", by_alias=True),
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
