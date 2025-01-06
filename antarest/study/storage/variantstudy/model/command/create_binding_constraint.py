# Copyright (c) 2024, RTE (https://www.rte-france.com)
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
from abc import ABCMeta
from enum import Enum

import numpy as np
from antares.study.version import StudyVersion
from pydantic import Field, field_validator, model_validator
from typing_extensions import override

from antarest.core.serialization import AntaresBaseModel
from antarest.matrixstore.model import MatrixData
from antarest.study.business.all_optional_meta import all_optional_model, camel_case_model
from antarest.study.model import STUDY_VERSION_8_3, STUDY_VERSION_8_7
from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import (
    DEFAULT_GROUP,
    DEFAULT_OPERATOR,
    DEFAULT_TIMESTEP,
    BindingConstraintFrequency,
    BindingConstraintOperator,
)
from antarest.study.storage.rawstudy.model.filesystem.config.field_validators import validate_filtering
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig, transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from antarest.study.storage.variantstudy.business.utils import validate_matrix
from antarest.study.storage.variantstudy.business.utils_binding_constraint import (
    parse_bindings_coeffs_and_save_into_config,
)
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import MATCH_SIGNATURE_SEPARATOR, ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO

MatrixType = t.List[t.List[MatrixData]]

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


# =================================================================================
# Binding constraint properties classes
# =================================================================================


class BindingConstraintPropertiesBase(AntaresBaseModel, extra="forbid", populate_by_name=True):
    enabled: bool = True
    time_step: BindingConstraintFrequency = Field(DEFAULT_TIMESTEP, alias="type")
    operator: BindingConstraintOperator = DEFAULT_OPERATOR
    comments: str = ""

    @model_validator(mode="before")
    def replace_with_alias(cls, values: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
        if "type" in values:
            values["time_step"] = values.pop("type")
        return values


class BindingConstraintProperties830(BindingConstraintPropertiesBase):
    filter_year_by_year: str = Field("", alias="filter-year-by-year")
    filter_synthesis: str = Field("", alias="filter-synthesis")

    @field_validator("filter_synthesis", "filter_year_by_year", mode="before")
    def _validate_filtering(cls, v: t.Any) -> str:
        return validate_filtering(v)


class BindingConstraintProperties870(BindingConstraintProperties830):
    group: str = DEFAULT_GROUP


BindingConstraintProperties = t.Union[
    BindingConstraintPropertiesBase,
    BindingConstraintProperties830,
    BindingConstraintProperties870,
]


def get_binding_constraint_config_cls(study_version: StudyVersion) -> t.Type[BindingConstraintProperties]:
    """
    Retrieves the binding constraint configuration class based on the study version.
    """
    if study_version >= STUDY_VERSION_8_7:
        return BindingConstraintProperties870
    elif study_version >= STUDY_VERSION_8_3:
        return BindingConstraintProperties830
    else:
        return BindingConstraintPropertiesBase


def create_binding_constraint_config(study_version: StudyVersion, **kwargs: t.Any) -> BindingConstraintProperties:
    """
    Factory method to create a binding constraint configuration model.

    Args:
        study_version: The version of the study.
        **kwargs: The properties to be used to initialize the model.

    Returns:
        The binding_constraint configuration model.
    """
    cls = get_binding_constraint_config_cls(study_version)
    attrs = {k: v for k, v in kwargs.items() if k in cls.model_fields and v is not None}
    return cls(**attrs)


@all_optional_model
class OptionalProperties(BindingConstraintProperties870):
    pass


# =================================================================================
# Binding constraint matrices classes
# =================================================================================


@camel_case_model
class BindingConstraintMatrices(AntaresBaseModel, extra="forbid", populate_by_name=True):
    """
    Class used to store the matrices of a binding constraint.
    """

    values: t.Optional[t.Union[MatrixType, str]] = Field(
        default=None,
        description="2nd member matrix for studies before v8.7",
    )
    less_term_matrix: t.Optional[t.Union[MatrixType, str]] = Field(
        default=None,
        description="less term matrix for v8.7+ studies",
    )
    greater_term_matrix: t.Optional[t.Union[MatrixType, str]] = Field(
        default=None,
        description="greater term matrix for v8.7+ studies",
    )
    equal_term_matrix: t.Optional[t.Union[MatrixType, str]] = Field(
        default=None,
        description="equal term matrix for v8.7+ studies",
    )

    @model_validator(mode="before")
    def check_matrices(
        cls, values: t.Dict[str, t.Optional[t.Union[MatrixType, str]]]
    ) -> t.Dict[str, t.Optional[t.Union[MatrixType, str]]]:
        values_matrix = values.get("values") or None
        less_term_matrix = values.get("less_term_matrix") or None
        greater_term_matrix = values.get("greater_term_matrix") or None
        equal_term_matrix = values.get("equal_term_matrix") or None
        if values_matrix and (less_term_matrix or greater_term_matrix or equal_term_matrix):
            raise ValueError(
                "You cannot fill 'values' (matrix before v8.7) and a matrix term:"
                " 'less_term_matrix', 'greater_term_matrix' or 'equal_term_matrix' (matrices since v8.7)"
            )

        return values


# =================================================================================
# Binding constraint command classes
# =================================================================================


class AbstractBindingConstraintCommand(OptionalProperties, BindingConstraintMatrices, ICommand, metaclass=ABCMeta):
    """
    Abstract class for binding constraint commands.
    """

    coeffs: t.Optional[t.Dict[str, t.List[float]]] = None

    @override
    def to_dto(self) -> CommandDTO:
        json_command = self.model_dump(mode="json", exclude={"command_context"})
        args = {}
        for field in ["enabled", "coeffs", "comments", "time_step", "operator"]:
            if json_command[field]:
                args[field] = json_command[field]

        # The `filter_year_by_year` and `filter_synthesis` attributes are only available for studies since v8.3
        if self.filter_synthesis:
            args["filter_synthesis"] = self.filter_synthesis
        if self.filter_year_by_year:
            args["filter_year_by_year"] = self.filter_year_by_year

        # The `group` attribute is only available for studies since v8.7
        if self.group:
            args["group"] = self.group

        matrix_service = self.command_context.matrix_service
        for matrix_name in [m.value for m in TermMatrices] + ["values"]:
            matrix_attr = getattr(self, matrix_name, None)
            if matrix_attr is not None:
                args[matrix_name] = matrix_service.get_matrix_id(matrix_attr)

        return CommandDTO(
            action=self.command_name.value, args=args, version=self.version, study_version=self.study_version
        )

    @override
    def get_inner_matrices(self) -> t.List[str]:
        matrix_service = self.command_context.matrix_service
        return [
            matrix_service.get_matrix_id(matrix)
            for matrix in [
                self.values,
                self.less_term_matrix,
                self.greater_term_matrix,
                self.equal_term_matrix,
            ]
            if matrix is not None
        ]

    def get_corresponding_matrices(
        self,
        v: t.Optional[t.Union[MatrixType, str]],
        time_step: BindingConstraintFrequency,
        version: StudyVersion,
        create: bool,
    ) -> t.Optional[str]:
        constants: GeneratorMatrixConstants = self.command_context.generator_matrix_constants

        if v is None:
            if not create:
                # The matrix is not updated
                return None
            # Use already-registered default matrix
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
            return methods["before_v87"][time_step]() if version < 870 else methods["after_v87"][time_step]()
        if isinstance(v, str):
            # Check the matrix link
            return validate_matrix(v, {"command_context": self.command_context})
        if isinstance(v, list):
            check_matrix_values(time_step, v, version)
            return validate_matrix(v, {"command_context": self.command_context})
        # Invalid datatype
        # pragma: no cover
        raise TypeError(repr(v))

    def validates_and_fills_matrices(
        self,
        *,
        time_step: BindingConstraintFrequency,
        specific_matrices: t.Optional[t.List[str]],
        version: StudyVersion,
        create: bool,
    ) -> None:
        if version < STUDY_VERSION_8_7:
            self.values = self.get_corresponding_matrices(self.values, time_step, version, create)
        elif specific_matrices:
            for matrix in specific_matrices:
                setattr(
                    self, matrix, self.get_corresponding_matrices(getattr(self, matrix), time_step, version, create)
                )
        else:
            self.less_term_matrix = self.get_corresponding_matrices(self.less_term_matrix, time_step, version, create)
            self.greater_term_matrix = self.get_corresponding_matrices(
                self.greater_term_matrix, time_step, version, create
            )
            self.equal_term_matrix = self.get_corresponding_matrices(self.equal_term_matrix, time_step, version, create)

    def apply_binding_constraint(
        self,
        study_data: FileStudy,
        binding_constraints: t.Dict[str, t.Any],
        new_key: str,
        bd_id: str,
        *,
        old_groups: t.Optional[t.Set[str]] = None,
    ) -> CommandOutput:
        version = study_data.config.version

        if self.coeffs:
            for link_or_cluster in self.coeffs:
                if "%" in link_or_cluster:
                    area_1, area_2 = link_or_cluster.split("%")
                    if area_1 not in study_data.config.areas or area_2 not in study_data.config.areas[area_1].links:
                        return CommandOutput(
                            status=False,
                            message=f"Link '{link_or_cluster}' does not exist in binding constraint '{bd_id}'",
                        )
                elif "." in link_or_cluster:
                    # Cluster IDs are stored in lower case in the binding constraints file.
                    area, cluster_id = link_or_cluster.split(".")
                    thermal_ids = {thermal.id.lower() for thermal in study_data.config.areas[area].thermals}
                    if area not in study_data.config.areas or cluster_id.lower() not in thermal_ids:
                        return CommandOutput(
                            status=False,
                            message=f"Cluster '{link_or_cluster}' does not exist in binding constraint '{bd_id}'",
                        )
                else:
                    raise NotImplementedError(f"Invalid link or thermal ID: {link_or_cluster}")

                # this is weird because Antares Simulator only accept int as offset
                if len(self.coeffs[link_or_cluster]) == 2:
                    self.coeffs[link_or_cluster][1] = int(self.coeffs[link_or_cluster][1])

                binding_constraints[new_key][link_or_cluster] = "%".join(
                    [str(coeff_val) for coeff_val in self.coeffs[link_or_cluster]]
                )

        study_data.tree.save(
            binding_constraints,
            ["input", "bindingconstraints", "bindingconstraints"],
        )

        existing_constraint = binding_constraints[new_key]
        current_operator = self.operator or BindingConstraintOperator(
            existing_constraint.get("operator", DEFAULT_OPERATOR)
        )
        group = self.group or existing_constraint.get("group", DEFAULT_GROUP)
        time_step = self.time_step or BindingConstraintFrequency(existing_constraint.get("type", DEFAULT_TIMESTEP))
        parse_bindings_coeffs_and_save_into_config(
            bd_id, study_data.config, self.coeffs or {}, operator=current_operator, time_step=time_step, group=group
        )

        if version >= STUDY_VERSION_8_7:
            # When all BC of a given group are removed, the group should be removed from the scenario builder
            old_groups = old_groups or set()
            new_groups = {bd.get("group", DEFAULT_GROUP).lower() for bd in binding_constraints.values()}
            removed_groups = old_groups - new_groups
            remove_bc_from_scenario_builder(study_data, removed_groups)

        if self.values:
            if not isinstance(self.values, str):  # pragma: no cover
                raise TypeError(repr(self.values))
            if version < STUDY_VERSION_8_7:
                study_data.tree.save(self.values, ["input", "bindingconstraints", bd_id])

        operator_matrices_map = {
            BindingConstraintOperator.EQUAL: [(self.equal_term_matrix, "eq")],
            BindingConstraintOperator.GREATER: [(self.greater_term_matrix, "gt")],
            BindingConstraintOperator.LESS: [(self.less_term_matrix, "lt")],
            BindingConstraintOperator.BOTH: [(self.less_term_matrix, "lt"), (self.greater_term_matrix, "gt")],
        }

        for matrix_term, matrix_alias in operator_matrices_map[current_operator]:
            if matrix_term:
                if not isinstance(matrix_term, str):  # pragma: no cover
                    raise TypeError(repr(matrix_term))
                if version >= STUDY_VERSION_8_7:
                    matrix_id = f"{bd_id}_{matrix_alias}"
                    study_data.tree.save(matrix_term, ["input", "bindingconstraints", matrix_id])
        return CommandOutput(status=True)

    @override
    def can_update_study_config(self) -> bool:
        return True


class CreateBindingConstraint(AbstractBindingConstraintCommand):
    """
    Command used to create a binding constraint.
    """

    command_name: CommandName = CommandName.CREATE_BINDING_CONSTRAINT
    version: int = 1

    # Properties of the `CREATE_BINDING_CONSTRAINT` command:
    name: str

    @override
    def _apply_config(self, study_data_config: FileStudyTreeConfig) -> t.Tuple[CommandOutput, t.Dict[str, t.Any]]:
        bd_id = transform_name_to_id(self.name)
        group = self.group or DEFAULT_GROUP
        operator = self.operator or DEFAULT_OPERATOR
        time_step = self.time_step or DEFAULT_TIMESTEP
        parse_bindings_coeffs_and_save_into_config(
            bd_id,
            study_data_config,
            self.coeffs or {},
            operator=operator,
            time_step=time_step,
            group=group,
        )
        return CommandOutput(status=True), {}

    @override
    def _apply(self, study_data: FileStudy, listener: t.Optional[ICommandListener] = None) -> CommandOutput:
        binding_constraints = study_data.tree.get(["input", "bindingconstraints", "bindingconstraints"])
        new_key = str(len(binding_constraints))
        bd_id = transform_name_to_id(self.name)

        study_version = study_data.config.version
        props = create_binding_constraint_config(**self.model_dump())
        obj = props.model_dump(mode="json", by_alias=True)

        new_binding = {"id": bd_id, "name": self.name, **obj}

        binding_constraints[new_key] = new_binding

        self.validates_and_fills_matrices(
            time_step=props.time_step, specific_matrices=None, version=study_version, create=True
        )
        return super().apply_binding_constraint(study_data, binding_constraints, new_key, bd_id)

    @override
    def to_dto(self) -> CommandDTO:
        dto = super().to_dto()
        dto.args["name"] = self.name  # type: ignore
        return dto

    @override
    def match_signature(self) -> str:
        return str(self.command_name.value + MATCH_SIGNATURE_SEPARATOR + self.name)

    @override
    def _create_diff(self, other: "ICommand") -> t.List["ICommand"]:
        from antarest.study.storage.variantstudy.model.command.update_binding_constraint import UpdateBindingConstraint

        other = t.cast(CreateBindingConstraint, other)
        bd_id = transform_name_to_id(self.name)
        args = {"id": bd_id, "command_context": other.command_context, "study_version": other.study_version}

        excluded_fields = set(ICommand.model_fields)
        self_command = self.model_dump(mode="json", exclude=excluded_fields)
        other_command = other.model_dump(mode="json", exclude=excluded_fields)
        properties = [
            "enabled",
            "coeffs",
            "comments",
            "filter_year_by_year",
            "filter_synthesis",
            "group",
            "time_step",
            "operator",
        ]
        for prop in properties:
            if self_command[prop] != other_command[prop]:
                args[prop] = other_command[prop]

        matrix_service = self.command_context.matrix_service
        for matrix_name in ["values"] + [m.value for m in TermMatrices]:
            self_matrix = getattr(self, matrix_name)  # matrix, ID or `None`
            other_matrix = getattr(other, matrix_name)  # matrix, ID or `None`
            self_matrix_id = None if self_matrix is None else matrix_service.get_matrix_id(self_matrix)
            other_matrix_id = None if other_matrix is None else matrix_service.get_matrix_id(other_matrix)
            if self_matrix_id != other_matrix_id:
                args[matrix_name] = other_matrix_id

        return [UpdateBindingConstraint.model_validate(args)]

    @override
    def match(self, other: "ICommand", equal: bool = False) -> bool:
        if not isinstance(other, self.__class__):
            return False
        if not equal:
            return self.name == other.name
        return super().match(other, equal)


def remove_bc_from_scenario_builder(study_data: FileStudy, removed_groups: t.Set[str]) -> None:
    """
    Update the scenario builder by removing the rows that correspond to the BC groups to remove.

    NOTE: this update can be very long if the scenario builder configuration is large.
    """
    if not removed_groups:
        return

    rulesets = study_data.tree.get(["settings", "scenariobuilder"])

    for ruleset in rulesets.values():
        for key in list(ruleset):
            # The key is in the form "symbol,group,year"
            symbol, *parts = key.split(",")
            if symbol == "bc" and parts[0] in removed_groups:
                del ruleset[key]

    study_data.tree.save(rulesets, ["settings", "scenariobuilder"])
