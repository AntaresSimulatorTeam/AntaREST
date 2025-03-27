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


from typing import Any, Dict, Final, List, Optional, Tuple, TypeAlias, cast

import numpy as np
from antares.study.version import StudyVersion
from pydantic import Field, model_validator
from typing_extensions import override

from antarest.core.model import JSON
from antarest.matrixstore.model import MatrixData
from antarest.study.model import STUDY_VERSION_8_6, STUDY_VERSION_9_2
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.config.model import Area, FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.config.st_storage import (
    STStoragePropertiesType,
    create_st_storage_config,
    create_st_storage_properties,
)
from antarest.study.storage.rawstudy.model.filesystem.config.validation import AreaId
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from antarest.study.storage.variantstudy.business.utils import strip_matrix_protocol, validate_matrix
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO

# Minimum required version.
REQUIRED_VERSION = STUDY_VERSION_8_6

MatrixType: TypeAlias = Optional[list[list[MatrixData]] | str]


# noinspection SpellCheckingInspection
class CreateSTStorage(ICommand):
    """
    Command used to create a short-terme storage in an area.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.CREATE_ST_STORAGE

    # version 2: parameters changed from STStorageConfigType to STStoragePropertiesType
    #            This actually did not require a version increment, but was done by mistake.
    _SERIALIZATION_VERSION: Final[int] = 2

    # Command parameters
    # ==================

    area_id: AreaId
    parameters: STStoragePropertiesType
    pmax_injection: MatrixType = Field(
        default=None,
        description="Charge capacity (modulation)",
    )
    pmax_withdrawal: MatrixType = Field(
        default=None,
        description="Discharge capacity (modulation)",
    )
    lower_rule_curve: MatrixType = Field(
        default=None,
        description="Lower rule curve (coefficient)",
    )
    upper_rule_curve: MatrixType = Field(
        default=None,
        description="Upper rule curve (coefficient)",
    )
    inflows: MatrixType = Field(
        default=None,
        description="Inflows (MW)",
    )
    cost_injection: MatrixType = Field(
        default=None,
        description="Charge Cost (€/MWh)",
    )
    cost_withdrawal: MatrixType = Field(
        default=None,
        description="Discharge Cost (€/MWh)",
    )
    cost_level: MatrixType = Field(
        default=None,
        description="Level Cost (€/MWh)",
    )
    cost_variation_injection: MatrixType = Field(
        default=None,
        description="Cost of injection variation (€/MWh)",
    )
    cost_variation_withdrawal: MatrixType = Field(
        default=None,
        description="Cost of withdrawal variation (€/MWh)",
    )

    @property
    def storage_id(self) -> str:
        """The normalized version of the storage's name used as the ID."""
        return transform_name_to_id(self.storage_name)

    @property
    def storage_name(self) -> str:
        """The label representing the name of the storage for the user."""
        return self.parameters.name

    @model_validator(mode="before")
    @classmethod
    def validate_model(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(values["parameters"], dict):
            properties_as_dict = values["parameters"]
        else:
            properties_as_dict = values["parameters"].model_dump(mode="json", exclude_unset=True)
        study_version = StudyVersion.parse(values["study_version"])
        values["parameters"] = create_st_storage_properties(study_version, data=properties_as_dict)
        return values

    def validate_field(self, v: MatrixType, field: str) -> MatrixType:
        """
        Validates a matrix array or link, and store the matrix array in the matrix repository.

        This method is used to validate the matrix array or link provided as input.

        - If the input is `None`, it retrieves a default matrix from the
          generator matrix constants.
        - If the input is a string, it validates the matrix link.
        - If the input is a list of lists, it validates the matrix values
          and creates the corresponding matrix link.

        Args:
            v: The matrix array or link to be validated and registered.
            field: The name of the validated parameter

        Returns:
            The ID of the validated and stored matrix prefixed by "matrix://".

        Raises:
            ValueError: If the matrix has an invalid shape, contains NaN values,
                or violates specific constraints.
            TypeError: If the input datatype is not supported.
        """
        values = {"command_context": self.command_context}
        if v is None:
            # use an already-registered default matrix
            constants: GeneratorMatrixConstants
            constants = self.command_context.generator_matrix_constants
            # Directly access the methods instead of using `getattr` for maintainability
            methods = {
                "pmax_injection": constants.get_st_storage_pmax_injection,
                "pmax_withdrawal": constants.get_st_storage_pmax_withdrawal,
                "lower_rule_curve": constants.get_st_storage_lower_rule_curve,
                "upper_rule_curve": constants.get_st_storage_upper_rule_curve,
                "inflows": constants.get_st_storage_inflows,
            }
            method = methods.get(field, lambda: None)
            return method()
        if isinstance(v, str):
            # Check the matrix link
            return validate_matrix(v, values)
        if isinstance(v, list):
            # Check the matrix values and create the corresponding matrix link
            array = np.array(v, dtype=np.float64)
            if array.shape != (8760, 1):
                raise ValueError(f"Invalid matrix shape {array.shape}, expected (8760, 1)")
            if np.isnan(array).any():
                raise ValueError("Matrix values cannot contain NaN")
            # All matrices except "inflows" are constrained between 0 and 1
            constrained = ["pmax_injection", "pmax_withdrawal", "lower_rule_curve", "upper_rule_curve"]
            if field in constrained and (np.any(array < 0) or np.any(array > 1)):
                raise ValueError("Matrix values should be between 0 and 1")
            v = cast(list[list[MatrixData]], array.tolist())
            return validate_matrix(v, values)
        # Invalid datatype
        # pragma: no cover
        raise TypeError(repr(v))

    def get_9_2_matrices(self) -> list[tuple[str, MatrixType]]:
        return [
            ("cost_injection", self.cost_injection),
            ("cost_withdrawal", self.cost_withdrawal),
            ("cost_level", self.cost_level),
            ("cost_variation_injection", self.cost_variation_injection),
            ("cost_variation_withdrawal", self.cost_variation_withdrawal),
        ]

    def get_matrices(self) -> list[tuple[str, MatrixType]]:
        matrices = [
            ("pmax_injection", self.pmax_injection),
            ("pmax_withdrawal", self.pmax_withdrawal),
            ("lower_rule_curve", self.lower_rule_curve),
            ("upper_rule_curve", self.upper_rule_curve),
            ("inflows", self.inflows),
        ]
        if self.study_version >= STUDY_VERSION_9_2:
            matrices.extend(self.get_9_2_matrices())
        return matrices

    @model_validator(mode="after")
    def validate_matrices(self) -> "CreateSTStorage":
        if self.study_version < STUDY_VERSION_9_2:
            for matrix_name, data in self.get_9_2_matrices():
                if data is not None:
                    raise ValueError(
                        f"You gave a 9.2 matrix: '{matrix_name}' for a study in version {self.study_version}"
                    )

        for matrix_name, matrix_data in self.get_matrices():
            setattr(self, matrix_name, self.validate_field(matrix_data, matrix_name))

        return self

    @override
    def _apply_config(self, study_data: FileStudyTreeConfig) -> Tuple[CommandOutput, Dict[str, Any]]:
        """
        Applies configuration changes to the study data: add the short-term storage in the storages list.

        Args:
            study_data: The study data configuration.

        Returns:
            A tuple containing the command output and a dictionary of extra data.
            On success, the dictionary of extra data is `{"storage_id": storage_id}`.
        """

        # Check if the study version is above the minimum required version.
        storage_id = self.storage_id
        version = study_data.version
        if version < REQUIRED_VERSION:
            return (
                CommandOutput(
                    status=False,
                    message=f"Invalid study version {version}, at least version {REQUIRED_VERSION} is required.",
                ),
                {},
            )

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

        # Check if the short-term storage already exists in the area
        if any(s.id == storage_id for s in area.st_storages):
            return (
                CommandOutput(
                    status=False,
                    message=f"Short-term storage '{self.storage_name}' already exists in the area '{self.area_id}'.",
                ),
                {},
            )

        # Create a new short-term storage and add it to the area
        storage_config = create_st_storage_config(
            self.study_version, **self.parameters.model_dump(mode="json", by_alias=True)
        )
        area.st_storages.append(storage_config)

        return (
            CommandOutput(
                status=True,
                message=f"Short-term st_storage '{self.storage_name}' successfully added to area '{self.area_id}'.",
            ),
            {"storage_id": storage_id},
        )

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        """
        Applies the study data to update storage configurations and saves the changes.

        Saves the changes made to the storage configurations.

        Args:
            study_data: The study data to be applied.

        Returns:
            The output of the command execution.
        """
        storage_id = self.storage_id
        output, _ = self._apply_config(study_data.config)
        if not output.status:
            return output

        # Fill-in the "list.ini" file with the parameters.
        # On creation, it's better to write all the parameters in the file.
        config = study_data.tree.get(["input", "st-storage", "clusters", self.area_id, "list"])
        config[storage_id] = self.parameters.model_dump(mode="json", by_alias=True)

        new_data: JSON = {
            "input": {
                "st-storage": {
                    "clusters": {self.area_id: {"list": config}},
                    "series": {
                        self.area_id: {storage_id: {attr: getattr(self, attr) or {} for attr, _ in self.get_matrices()}}
                    },
                }
            }
        }
        study_data.tree.save(new_data)

        return output

    @override
    def to_dto(self) -> CommandDTO:
        """
        Converts the current object to a Data Transfer Object (DTO)
        which is stored in the `CommandBlock` in the database.

        Returns:
            The DTO object representing the current command.
        """
        args = {"area_id": self.area_id, "parameters": self.parameters.model_dump(mode="json", by_alias=True)}
        for attr, _ in self.get_matrices():
            if getattr(self, attr) is not None:
                args[attr] = strip_matrix_protocol(getattr(self, attr))
        return CommandDTO(
            action=self.command_name.value,
            version=self._SERIALIZATION_VERSION,
            args=args,
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        """
        Retrieves the list of matrix IDs.
        """
        matrices: List[str] = []
        for attr, _ in self.get_matrices():
            if getattr(self, attr) is not None:
                matrices.append(strip_matrix_protocol(getattr(self, attr)))
        return matrices
