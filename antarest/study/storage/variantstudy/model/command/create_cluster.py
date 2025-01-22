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

from pydantic import Field, model_validator
from typing_extensions import override

from antarest.core.model import JSON
from antarest.core.utils.utils import assert_this
from antarest.matrixstore.model import MatrixData
from antarest.study.model import STUDY_VERSION_8_7
from antarest.study.storage.rawstudy.model.filesystem.config.field_validators import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.config.model import Area, FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.config.thermal import (
    ThermalPropertiesType,
    create_thermal_config,
    create_thermal_properties,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.utils import strip_matrix_protocol, validate_matrix
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import MATCH_SIGNATURE_SEPARATOR, ICommand
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
    parameters: ThermalPropertiesType
    prepro: t.Optional[t.Union[t.List[t.List[MatrixData]], str]] = Field(None, validate_default=True)
    modulation: t.Optional[t.Union[t.List[t.List[MatrixData]], str]] = Field(None, validate_default=True)

    @model_validator(mode="before")
    def validate_model(cls, values: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
        # Validate parameters
        args = {"name": values["cluster_name"], **values["parameters"]}
        values["parameters"] = create_thermal_properties(values["study_version"], **args)

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
    def _apply_config(self, study_data: FileStudyTreeConfig) -> t.Tuple[CommandOutput, t.Dict[str, t.Any]]:
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
    def _apply(self, study_data: FileStudy, listener: t.Optional[ICommandListener] = None) -> CommandOutput:
        output, data = self._apply_config(study_data.config)
        if not output.status:
            return output

        version = study_data.config.version

        cluster_id = data["cluster_id"]
        config = study_data.tree.get(["input", "thermal", "clusters", self.area_id, "list"])
        config[self.cluster_name] = self.parameters.model_dump(mode="json", by_alias=True)

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
            action=self.command_name.value,
            args={
                "area_id": self.area_id,
                "cluster_name": self.cluster_name,
                "parameters": self.parameters.model_dump(mode="json", by_alias=True),
                "prepro": strip_matrix_protocol(self.prepro),
                "modulation": strip_matrix_protocol(self.modulation),
            },
            study_version=self.study_version,
        )

    @override
    def match_signature(self) -> str:
        return str(
            self.command_name.value
            + MATCH_SIGNATURE_SEPARATOR
            + self.area_id
            + MATCH_SIGNATURE_SEPARATOR
            + self.cluster_name
        )

    @override
    def match(self, other: ICommand, equal: bool = False) -> bool:
        if not isinstance(other, CreateCluster):
            return False
        simple_match = self.area_id == other.area_id and self.cluster_name == other.cluster_name
        if not equal:
            return simple_match
        self_params = self.parameters.model_dump(mode="json", by_alias=True)
        other_params = other.parameters.model_dump(mode="json", by_alias=True)
        return (
            simple_match
            and self_params == other_params
            and self.prepro == other.prepro
            and self.modulation == other.modulation
        )

    @override
    def _create_diff(self, other: "ICommand") -> t.List["ICommand"]:
        other = t.cast(CreateCluster, other)
        from antarest.study.storage.variantstudy.model.command.replace_matrix import ReplaceMatrix
        from antarest.study.storage.variantstudy.model.command.update_config import UpdateConfig

        # Series identifiers are in lower case.
        series_id = transform_name_to_id(self.cluster_name)
        commands: t.List[ICommand] = []
        if self.prepro != other.prepro:
            commands.append(
                ReplaceMatrix(
                    target=f"input/thermal/prepro/{self.area_id}/{series_id}/data",
                    matrix=strip_matrix_protocol(other.prepro),
                    command_context=self.command_context,
                    study_version=self.study_version,
                )
            )
        if self.modulation != other.modulation:
            commands.append(
                ReplaceMatrix(
                    target=f"input/thermal/prepro/{self.area_id}/{series_id}/modulation",
                    matrix=strip_matrix_protocol(other.modulation),
                    command_context=self.command_context,
                    study_version=self.study_version,
                )
            )
        self_params = self.parameters.model_dump(mode="json", by_alias=True)
        other_params = other.parameters.model_dump(mode="json", by_alias=True)
        if self_params != other_params:
            commands.append(
                UpdateConfig(
                    target=f"input/thermal/clusters/{self.area_id}/list/{self.cluster_name}",
                    data=other_params,
                    command_context=self.command_context,
                    study_version=self.study_version,
                )
            )
        return commands

    @override
    def get_inner_matrices(self) -> t.List[str]:
        matrices: t.List[str] = []
        if self.prepro:
            assert_this(isinstance(self.prepro, str))
            matrices.append(strip_matrix_protocol(self.prepro))
        if self.modulation:
            assert_this(isinstance(self.modulation, str))
            matrices.append(strip_matrix_protocol(self.modulation))
        return matrices
