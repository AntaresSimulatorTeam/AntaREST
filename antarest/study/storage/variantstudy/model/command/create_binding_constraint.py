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

from abc import ABCMeta
from enum import Enum
from typing import Any, Dict, Final, List, Optional, Self, TypeAlias

import numpy as np
from antares.study.version import StudyVersion
from pydantic import model_validator
from pydantic_core.core_schema import ValidationInfo
from typing_extensions import override

from antarest.core.exceptions import InvalidFieldForVersionError
from antarest.matrixstore.model import MatrixData
from antarest.study.business.model.binding_constraint_model import (
    DEFAULT_TIMESTEP,
    BindingConstraintCreation,
    BindingConstraintFrequency,
    BindingConstraintMatrices,
    BindingConstraintOperator,
    BindingConstraintUpdate,
    ClusterTerm,
    ConstraintTerm,
    LinkTerm,
    create_binding_constraint,
    validate_binding_constraint_against_version,
)
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.model import STUDY_VERSION_8_7
from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import parse_binding_constraint
from antarest.study.storage.rawstudy.model.filesystem.config.identifier import transform_name_to_id
from antarest.study.storage.variantstudy.business.utils import strip_matrix_protocol, validate_matrix
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput, command_succeeded
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO

MatrixType: TypeAlias = List[List[MatrixData]]

EXPECTED_MATRIX_SHAPES = {
    BindingConstraintFrequency.HOURLY: (8784, 3),
    BindingConstraintFrequency.DAILY: (366, 3),
    BindingConstraintFrequency.WEEKLY: (366, 3),
}


class TermMatrices(Enum):
    LESS = "less_term_matrix"
    GREATER = "greater_term_matrix"
    EQUAL = "equal_term_matrix"


def check_matrix_values(time_step: BindingConstraintFrequency, values: MatrixType, version: StudyVersion) -> None:
    """
    Check the binding constraint's matrix values for the specified time step.

    Args:
        time_step: The frequency of the binding constraint: "hourly", "daily" or "weekly".
        values: The binding constraint's 2nd member matrix.
        version: Study version.

    Raises:
        ValueError:
            If the matrix shape does not match the expected shape for the given time step.
            If the matrix values contain NaN (Not-a-Number).
    """
    # Matrix shapes for binding constraints are different from usual shapes,
    # because we need to take leap years into account, which contains 366 days and 8784 hours.
    # Also, we use the same matrices for "weekly" and "daily" frequencies,
    # because the solver calculates the weekly matrix from the daily matrix.
    # See https://github.com/AntaresSimulatorTeam/AntaREST/issues/1843
    # Check the matrix values and create the corresponding matrix link
    array = np.array(values, dtype=np.float64)
    expected_shape = EXPECTED_MATRIX_SHAPES[time_step]
    actual_shape = array.shape
    if version < 870:
        if actual_shape != expected_shape:
            raise ValueError(f"Invalid matrix shape {actual_shape}, expected {expected_shape}")
    elif actual_shape[0] != expected_shape[0]:
        raise ValueError(f"Invalid matrix length {actual_shape[0]}, expected {expected_shape[0]}")
    if np.isnan(array).any():
        raise ValueError("Matrix values cannot contain NaN")


def get_parameters_keys() -> set[str]:
    """Used to parse legacy commands"""
    parameters = BindingConstraintCreation(name="a")
    parameters_keys = parameters.model_dump()
    parameters_keys.update(parameters.model_dump(by_alias=True))
    del parameters_keys["terms"]
    parameters_keys["type"] = ""
    return set(parameters_keys)


def get_matrices_keys() -> set[str]:
    """Used to parse legacy commands"""
    matrices = BindingConstraintMatrices()
    matrices_keys = matrices.model_dump()
    matrices_keys.update(matrices.model_dump(by_alias=True))
    return set(matrices_keys)


# =================================================================================
# Binding constraint command classes
# =================================================================================


class AbstractBindingConstraintCommand(ICommand, metaclass=ABCMeta):
    """
    Abstract class for binding constraint commands.
    """

    _SERIALIZATION_VERSION: Final[int] = 2

    def get_corresponding_matrix(self, value: MatrixType, time_step: BindingConstraintFrequency) -> str:
        check_matrix_values(time_step, value, self.study_version)
        return validate_matrix(value, {"command_context": self.command_context})

    def validate_matrix(self, v: Optional[MatrixType | str], time_step: BindingConstraintFrequency) -> Optional[str]:
        if v is None:
            return None
        if isinstance(v, str):
            # Check the matrix link
            return validate_matrix(strip_matrix_protocol(v), {"command_context": self.command_context})
        if isinstance(v, list):
            check_matrix_values(time_step, v, self.study_version)
            return validate_matrix(v, {"command_context": self.command_context})
        # Invalid datatype
        # pragma: no cover
        raise TypeError(repr(v))

    @staticmethod
    def convert_coeffs_to_terms(coeffs: dict[str, list[float]]) -> list[ConstraintTerm]:
        terms = []
        for link_or_cluster, w_o in coeffs.items():
            weight = w_o[0]
            offset = w_o[1] if len(w_o) == 2 else None
            if "%" in link_or_cluster:
                area_1, area_2 = link_or_cluster.split("%")
                terms.append(
                    ConstraintTerm(
                        weight=weight,
                        offset=offset,
                        data=LinkTerm.model_validate(
                            {
                                "area1": area_1,
                                "area2": area_2,
                            }
                        ),
                    )
                )
            elif "." in link_or_cluster:
                area, cluster_id = link_or_cluster.split(".")
                terms.append(
                    ConstraintTerm(
                        weight=weight,
                        offset=offset,
                        data=ClusterTerm.model_validate({"area": area, "cluster": cluster_id}),
                    )
                )
            else:
                raise NotImplementedError(f"Invalid link or thermal ID: {link_or_cluster}")
        return terms

    def command_get_inner_matrices(self, matrices: BindingConstraintMatrices) -> list[str]:
        matrix_service = self.command_context.matrix_service
        return [
            matrix_service.get_matrix_id(matrix)
            for matrix in [
                matrices.values,
                matrices.less_term_matrix,
                matrices.greater_term_matrix,
                matrices.equal_term_matrix,
            ]
            if matrix is not None
        ]

    def command_to_dto(
        self, parameters: BindingConstraintCreation | BindingConstraintUpdate, matrices: BindingConstraintMatrices
    ) -> CommandDTO:
        return CommandDTO(
            version=self._SERIALIZATION_VERSION,
            action=self.command_name.value,
            args={
                "parameters": parameters.model_dump(mode="json", by_alias=True, exclude_none=True),
                "matrices": matrices.model_dump(mode="json", by_alias=True, exclude_none=True),
            },
            study_version=self.study_version,
        )

    def check_matrices_column_sizes_coherence(self, matrices: BindingConstraintMatrices) -> None:
        if self.study_version < STUDY_VERSION_8_7:
            return

        all_cols_sizes = {}

        for term_name in [m.value for m in TermMatrices]:
            if isinstance(getattr(matrices, term_name), list):
                term_size = len(getattr(matrices, term_name)[0])
                if term_size > 1:
                    all_cols_sizes[term_size] = term_name

        if len(all_cols_sizes) > 1:
            # Prepare a clear error message
            _field_names = ", ".join(f"'{n}'" for n in all_cols_sizes.values())
            _cols_size = ", ".join(f"'{n}'" for n in all_cols_sizes.keys())
            err_msg = f"Matrices {_field_names} must have the same column sizes: {_cols_size}"
            raise ValueError(err_msg)


class CreateBindingConstraint(AbstractBindingConstraintCommand):
    """
    Command used to create a binding constraint.
    """

    command_name: CommandName = CommandName.CREATE_BINDING_CONSTRAINT

    # version 2: put all args inside `parameters` and type it as BindingConstraintCreation + put all matrices inside `matrices`

    parameters: BindingConstraintCreation
    matrices: BindingConstraintMatrices

    @model_validator(mode="before")
    @classmethod
    def _validate_model_before(cls, values: Dict[str, Any], info: ValidationInfo) -> Dict[str, Any]:
        if info.context:
            version = info.context.version
            if version == 1:
                study_version = StudyVersion.parse(values["study_version"])

                # Validate parameters
                parameters_keys = get_parameters_keys()
                args = {}
                for key in list(values.keys()):
                    if key in parameters_keys:
                        args[key] = values.pop(key)
                if "coeffs" in values:
                    args["terms"] = cls.convert_coeffs_to_terms(values.pop("coeffs"))
                args["id"] = transform_name_to_id(args["name"])
                constraint = parse_binding_constraint(study_version, args)
                values["parameters"] = BindingConstraintCreation.from_constraint(constraint)

                # Validate matrices
                values["matrices"] = {}
                matrices_keys = get_matrices_keys()
                for key in list(values.keys()):
                    if key in matrices_keys:
                        values["matrices"][key] = values.pop(key)

        return values

    @model_validator(mode="after")
    def _validate_model_after(self) -> Self:
        # Validate parameters
        validate_binding_constraint_against_version(self.study_version, self.parameters)

        # Validate matrices
        time_step = self.parameters.time_step or DEFAULT_TIMESTEP

        if self.study_version < STUDY_VERSION_8_7:
            for matrix in [m.value for m in TermMatrices]:
                if getattr(self.matrices, matrix) is not None:
                    raise InvalidFieldForVersionError(
                        "You cannot fill a 'matrix_term' as these values refer to v8.7+ studies"
                    )

            self.matrices.values = self.validate_matrix(self.matrices.values, time_step)

        else:
            if self.matrices.values is not None:
                raise InvalidFieldForVersionError("You cannot fill 'values' as it refers to the matrix before v8.7")

            super().check_matrices_column_sizes_coherence(self.matrices)

            self.matrices.less_term_matrix = self.validate_matrix(self.matrices.less_term_matrix, time_step)
            self.matrices.greater_term_matrix = self.validate_matrix(self.matrices.greater_term_matrix, time_step)
            self.matrices.equal_term_matrix = self.validate_matrix(self.matrices.equal_term_matrix, time_step)

        return self

    @override
    def _apply_dao(self, study_data: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
        constraint = create_binding_constraint(self.parameters, self.study_version)
        study_data.save_constraints([constraint])

        # Matrices
        default_matrix = self._create_default_matrix(constraint.time_step)

        if self.study_version < STUDY_VERSION_8_7:
            matrix = default_matrix if not self.matrices.values else self.matrices.values
            assert isinstance(matrix, str)
            study_data.save_constraint_values_matrix(constraint.id, matrix)

        else:
            operator = constraint.operator
            if operator == BindingConstraintOperator.EQUAL:
                matrix = default_matrix if not self.matrices.equal_term_matrix else self.matrices.equal_term_matrix
                assert isinstance(matrix, str)
                study_data.save_constraint_equal_term_matrix(constraint.id, matrix)

            if operator in {BindingConstraintOperator.GREATER, BindingConstraintOperator.BOTH}:
                matrix = default_matrix if not self.matrices.greater_term_matrix else self.matrices.greater_term_matrix
                assert isinstance(matrix, str)
                study_data.save_constraint_greater_term_matrix(constraint.id, matrix)

            if operator in {BindingConstraintOperator.LESS, BindingConstraintOperator.BOTH}:
                matrix = default_matrix if not self.matrices.less_term_matrix else self.matrices.less_term_matrix
                assert isinstance(matrix, str)
                study_data.save_constraint_less_term_matrix(constraint.id, matrix)

        return command_succeeded(f"Binding constraint '{constraint.id}' created successfully.")

    @override
    def to_dto(self) -> CommandDTO:
        return super().command_to_dto(self.parameters, self.matrices)

    @override
    def get_inner_matrices(self) -> List[str]:
        return super().command_get_inner_matrices(self.matrices)

    def _create_default_matrix(self, time_step: BindingConstraintFrequency) -> str:
        constants = self.command_context.generator_matrix_constants
        methods = {
            "before_v87": {
                BindingConstraintFrequency.HOURLY: constants.get_binding_constraint_hourly_86,
                BindingConstraintFrequency.DAILY: constants.get_binding_constraint_daily_weekly_86,
                BindingConstraintFrequency.WEEKLY: constants.get_binding_constraint_daily_weekly_86,
            },
            "after_v87": {
                BindingConstraintFrequency.HOURLY: constants.get_binding_constraint_hourly_87,
                BindingConstraintFrequency.DAILY: constants.get_binding_constraint_daily_weekly_87,
                BindingConstraintFrequency.WEEKLY: constants.get_binding_constraint_daily_weekly_87,
            },
        }
        return (
            methods["before_v87"][time_step]()
            if self.study_version < STUDY_VERSION_8_7
            else methods["after_v87"][time_step]()
        )
