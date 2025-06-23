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

from typing import Any, Optional, Self

from antares.study.version import StudyVersion
from pydantic import model_validator
from pydantic_core.core_schema import ValidationInfo
from typing_extensions import override

from antarest.core.exceptions import InvalidFieldForVersionError
from antarest.study.business.model.binding_constraint_model import (
    BindingConstraintFrequency,
    BindingConstraintMatrices,
    BindingConstraintOperator,
    BindingConstraintUpdate,
    update_binding_constraint,
    validate_binding_constraint_against_version,
)
from antarest.study.dao.api.study_dao import StudyDao
from antarest.study.model import STUDY_VERSION_8_7
from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import (
    parse_binding_constraint_for_update,
)
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput, command_succeeded
from antarest.study.storage.variantstudy.model.command.create_binding_constraint import (
    AbstractBindingConstraintCommand,
    TermMatrices,
    get_matrices_keys,
    get_parameters_keys,
)
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class UpdateBindingConstraint(AbstractBindingConstraintCommand):
    """
    Command used to update a binding constraint.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_BINDING_CONSTRAINT

    # Command parameters
    # ==================

    # Properties of the `UPDATE_BINDING_CONSTRAINT` command:
    id: str

    # version 2: put all args inside `parameters` and type it as BindingConstraintCreation + put all matrices inside `matrices`

    parameters: BindingConstraintUpdate
    matrices: BindingConstraintMatrices

    @model_validator(mode="before")
    @classmethod
    def _validate_model_before(cls, values: dict[str, Any], info: ValidationInfo) -> dict[str, Any]:
        if info.context:
            version = info.context.version
            if version == 1:
                # We need to handle the legacy format for already existing commands in the database.
                study_version = StudyVersion.parse(values["study_version"])

                # Validate parameters
                parameters_keys = get_parameters_keys()
                args = {}
                for key in list(values.keys()):
                    if key in parameters_keys:
                        args[key] = values.pop(key)
                if "coeffs" in values:
                    args["terms"] = cls.convert_coeffs_to_terms(values.pop("coeffs"))
                args.update({"id": values["id"], "name": values["id"]})
                values["parameters"] = parse_binding_constraint_for_update(study_version, args)

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
        if self.study_version < STUDY_VERSION_8_7:
            for matrix in [m.value for m in TermMatrices]:
                if getattr(self.matrices, matrix) is not None:
                    raise InvalidFieldForVersionError(
                        "You cannot fill a 'matrix_term' as these values refer to v8.7+ studies"
                    )
        else:
            if self.matrices.values is not None:
                raise InvalidFieldForVersionError("You cannot fill 'values' as it refers to the matrix before v8.7")
            super().check_matrices_column_sizes_coherence(self.matrices)

        return self

    def _validate_and_fill_matrices(self, time_step: BindingConstraintFrequency) -> None:
        if self.study_version < STUDY_VERSION_8_7:
            self.matrices.values = self.validate_matrix(self.matrices.values, time_step)
        else:
            self.matrices.less_term_matrix = self.validate_matrix(self.matrices.less_term_matrix, time_step)
            self.matrices.greater_term_matrix = self.validate_matrix(self.matrices.greater_term_matrix, time_step)
            self.matrices.equal_term_matrix = self.validate_matrix(self.matrices.equal_term_matrix, time_step)

    @override
    def _apply_dao(self, study_data: StudyDao, listener: Optional[ICommandListener] = None) -> CommandOutput:
        current_constraint = study_data.get_constraint(self.id)
        constraint = update_binding_constraint(current_constraint, self.parameters)

        self._validate_and_fill_matrices(constraint.time_step)

        study_data.save_constraints([constraint])

        # Matrices
        if self.study_version < STUDY_VERSION_8_7:
            if self.matrices.values:
                assert isinstance(self.matrices.values, str)
                study_data.save_constraint_values_matrix(constraint.id, self.matrices.values)
        else:
            operator = constraint.operator
            if operator == BindingConstraintOperator.EQUAL:
                if self.matrices.equal_term_matrix:
                    assert isinstance(self.matrices.equal_term_matrix, str)
                    study_data.save_constraint_equal_term_matrix(constraint.id, self.matrices.equal_term_matrix)

            if operator in {BindingConstraintOperator.GREATER, BindingConstraintOperator.BOTH}:
                if self.matrices.greater_term_matrix:
                    assert isinstance(self.matrices.greater_term_matrix, str)
                    study_data.save_constraint_greater_term_matrix(constraint.id, self.matrices.greater_term_matrix)

            if operator in {BindingConstraintOperator.LESS, BindingConstraintOperator.BOTH}:
                if self.matrices.less_term_matrix:
                    assert isinstance(self.matrices.less_term_matrix, str)
                    study_data.save_constraint_less_term_matrix(constraint.id, self.matrices.less_term_matrix)

        return command_succeeded(f"Binding constraint '{constraint.id}' updated successfully.")

    @override
    def to_dto(self) -> CommandDTO:
        dto = super().command_to_dto(self.parameters, self.matrices)
        assert isinstance(dto.args, dict)
        dto.args["id"] = self.id
        return dto

    @override
    def get_inner_matrices(self) -> list[str]:
        return super().command_get_inner_matrices(self.matrices)
