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
from typing import Any, Dict, Final, List, Optional, Self

from antares.study.version import StudyVersion
from pydantic import Field, model_validator
from pydantic_core.core_schema import ValidationInfo
from typing_extensions import override

from antarest.core.utils.utils import assert_this
from antarest.matrixstore.model import MatrixData
from antarest.study.business.model.thermal_cluster_model import (
    ThermalClusterCreation,
    create_thermal_cluster,
    validate_thermal_cluster_against_version,
)
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.model import STUDY_VERSION_8_7
from antarest.study.storage.rawstudy.model.filesystem.config.thermal import (
    parse_thermal_cluster,
)
from antarest.study.storage.rawstudy.model.filesystem.config.validation import AreaId
from antarest.study.storage.variantstudy.business.utils import strip_matrix_protocol, validate_matrix
from antarest.study.storage.variantstudy.model.command.common import (
    CommandName,
    CommandOutput,
    command_failed,
    command_succeeded,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO

OptionalMatrixData: t.TypeAlias = List[List[MatrixData]] | str | None


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

    @model_validator(mode="before")
    @classmethod
    def _validate_model(cls, values: Dict[str, t.Any], info: ValidationInfo) -> Dict[str, Any]:
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

    @model_validator(mode="after")
    def _validate_against_version(self) -> Self:
        validate_thermal_cluster_against_version(self.study_version, self.parameters)
        return self

    @override
    def _apply_dao(self, study_data: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
        thermal = create_thermal_cluster(self.parameters, self.study_version)
        lower_thermal_id = thermal.id.lower()
        if study_data.thermal_exists(self.area_id, lower_thermal_id):
            return command_failed(f"Thermal cluster '{thermal.id}' already exists in the area '{self.area_id}'")

        study_data.save_thermal(self.area_id, thermal)

        # Matrices
        null_matrix = self.command_context.generator_matrix_constants.get_null_matrix()
        study_data.save_thermal_series(self.area_id, lower_thermal_id, null_matrix)
        assert isinstance(self.prepro, str)
        assert isinstance(self.modulation, str)
        study_data.save_thermal_prepro(self.area_id, lower_thermal_id, self.prepro)
        study_data.save_thermal_modulation(self.area_id, lower_thermal_id, self.modulation)
        if self.study_version >= STUDY_VERSION_8_7:
            study_data.save_thermal_fuel_cost(self.area_id, lower_thermal_id, null_matrix)
            study_data.save_thermal_co2_cost(self.area_id, lower_thermal_id, null_matrix)

        return command_succeeded(f"Thermal cluster '{thermal.id}' added to area '{self.area_id}'.")

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            version=self._SERIALIZATION_VERSION,
            action=self.command_name.value,
            args={
                "area_id": self.area_id,
                "parameters": self.parameters.model_dump(mode="json", by_alias=True, exclude_none=True),
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
