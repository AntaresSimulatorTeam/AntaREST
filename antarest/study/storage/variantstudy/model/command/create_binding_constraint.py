import typing as t
from abc import ABCMeta

import numpy as np
from pydantic import BaseModel, Extra, Field, root_validator

from antarest.matrixstore.model import MatrixData
from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import BindingConstraintFrequency
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig, transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from antarest.study.storage.variantstudy.business.utils import validate_matrix
from antarest.study.storage.variantstudy.business.utils_binding_constraint import (
    apply_binding_constraint,
    parse_bindings_coeffs_and_save_into_config,
)
from antarest.study.storage.variantstudy.model.command.common import (
    BindingConstraintOperator,
    CommandName,
    CommandOutput,
)
from antarest.study.storage.variantstudy.model.command.icommand import MATCH_SIGNATURE_SEPARATOR, ICommand
from antarest.study.storage.variantstudy.model.model import CommandDTO

__all__ = (
    "AbstractBindingConstraintCommand",
    "CreateBindingConstraint",
    "check_matrix_values",
    "BindingConstraintProperties",
    "BindingConstraintProperties870",
    "BindingConstraintMatrices",
)

MatrixType = t.List[t.List[MatrixData]]


def check_matrix_values(time_step: BindingConstraintFrequency, values: MatrixType, version: int) -> None:
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
    shapes = {
        BindingConstraintFrequency.HOURLY: (8784, 3),
        BindingConstraintFrequency.DAILY: (366, 3),
        BindingConstraintFrequency.WEEKLY: (366, 3),
    }
    # Check the matrix values and create the corresponding matrix link
    array = np.array(values, dtype=np.float64)
    expected_shape = shapes[time_step]
    actual_shape = array.shape
    if version < 870:
        if actual_shape != expected_shape:
            raise ValueError(f"Invalid matrix shape {actual_shape}, expected {expected_shape}")
    elif actual_shape[0] != expected_shape[0]:
        raise ValueError(f"Invalid matrix length {actual_shape[0]}, expected {expected_shape[0]}")
    if np.isnan(array).any():
        raise ValueError("Matrix values cannot contain NaN")


class BindingConstraintProperties(BaseModel, extra=Extra.forbid, allow_population_by_field_name=True):
    enabled: bool = True
    time_step: BindingConstraintFrequency = BindingConstraintFrequency.HOURLY
    operator: BindingConstraintOperator = BindingConstraintOperator.EQUAL
    comments: t.Optional[str] = ""
    filter_year_by_year: t.Optional[str] = ""
    filter_synthesis: t.Optional[str] = ""


class BindingConstraintProperties870(BindingConstraintProperties):
    group: t.Optional[str] = ""


class BindingConstraintMatrices(BaseModel, extra=Extra.forbid, allow_population_by_field_name=True):
    """
    Class used to store the matrices of a binding constraint.
    """

    values: t.Optional[t.Union[MatrixType, str]] = Field(
        None,
        description="2nd member matrix for studies before v8.7",
    )
    less_term_matrix: t.Optional[t.Union[MatrixType, str]] = Field(
        None,
        description="less term matrix for v8.7+ studies",
        alias="lessTermMatrix",
    )
    greater_term_matrix: t.Optional[t.Union[MatrixType, str]] = Field(
        None,
        description="greater term matrix for v8.7+ studies",
        alias="greaterTermMatrix",
    )
    equal_term_matrix: t.Optional[t.Union[MatrixType, str]] = Field(
        None,
        description="equal term matrix for v8.7+ studies",
        alias="equalTermMatrix",
    )

    @root_validator(pre=True)
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


class AbstractBindingConstraintCommand(
    BindingConstraintProperties870, BindingConstraintMatrices, ICommand, metaclass=ABCMeta
):
    """
    Abstract class for binding constraint commands.
    """

    coeffs: t.Dict[str, t.List[float]]

    def to_dto(self) -> CommandDTO:
        args = {
            "enabled": self.enabled,
            "time_step": self.time_step.value,
            "operator": self.operator.value,
            "coeffs": self.coeffs,
            "comments": self.comments,
            "filter_year_by_year": self.filter_year_by_year,
            "filter_synthesis": self.filter_synthesis,
        }

        # The `group` attribute is only available for studies since v8.7
        if self.group:
            args["group"] = self.group

        matrix_service = self.command_context.matrix_service
        for matrix_name in ["values", "less_term_matrix", "greater_term_matrix", "equal_term_matrix"]:
            matrix_attr = getattr(self, matrix_name, None)
            if matrix_attr is not None:
                args[matrix_name] = matrix_service.get_matrix_id(matrix_attr)

        return CommandDTO(action=self.command_name.value, args=args, version=self.version)

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
        self, v: t.Optional[t.Union[MatrixType, str]], version: int, create: bool
    ) -> t.Optional[str]:
        constants: GeneratorMatrixConstants
        constants = self.command_context.generator_matrix_constants
        time_step = self.time_step

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
        self, *, specific_matrices: t.Optional[t.List[str]], version: int, create: bool
    ) -> None:
        if version < 870:
            self.values = self.get_corresponding_matrices(self.values, version, create)
        elif specific_matrices:
            for matrix in specific_matrices:
                setattr(self, matrix, self.get_corresponding_matrices(getattr(self, matrix), version, create))
        else:
            self.less_term_matrix = self.get_corresponding_matrices(self.less_term_matrix, version, create)
            self.greater_term_matrix = self.get_corresponding_matrices(self.greater_term_matrix, version, create)
            self.equal_term_matrix = self.get_corresponding_matrices(self.equal_term_matrix, version, create)


class CreateBindingConstraint(AbstractBindingConstraintCommand):
    """
    Command used to create a binding constraint.
    """

    command_name = CommandName.CREATE_BINDING_CONSTRAINT
    version: int = 1

    # Properties of the `CREATE_BINDING_CONSTRAINT` command:
    name: str

    def _apply_config(self, study_data_config: FileStudyTreeConfig) -> t.Tuple[CommandOutput, t.Dict[str, t.Any]]:
        bd_id = transform_name_to_id(self.name)
        parse_bindings_coeffs_and_save_into_config(bd_id, study_data_config, self.coeffs)
        return CommandOutput(status=True), {}

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        binding_constraints = study_data.tree.get(["input", "bindingconstraints", "bindingconstraints"])
        new_key = len(binding_constraints)
        bd_id = transform_name_to_id(self.name)
        self.validates_and_fills_matrices(specific_matrices=None, version=study_data.config.version, create=True)

        return apply_binding_constraint(
            study_data,
            binding_constraints,
            str(new_key),
            bd_id,
            self.name,
            self.comments,
            self.enabled,
            self.time_step,
            self.operator,
            self.coeffs,
            self.values,
            self.less_term_matrix,
            self.greater_term_matrix,
            self.equal_term_matrix,
            self.filter_year_by_year,
            self.filter_synthesis,
            self.group,
        )

    def to_dto(self) -> CommandDTO:
        dto = super().to_dto()
        dto.args["name"] = self.name  # type: ignore
        return dto

    def match_signature(self) -> str:
        return str(self.command_name.value + MATCH_SIGNATURE_SEPARATOR + self.name)

    def match(self, other: ICommand, equal: bool = False) -> bool:
        if not isinstance(other, CreateBindingConstraint):
            return False
        simple_match = self.name == other.name
        if not equal:
            return simple_match
        return (
            simple_match
            and self.enabled == other.enabled
            and self.time_step == other.time_step
            and self.operator == other.operator
            and self.coeffs == other.coeffs
            and self.values == other.values
            and self.comments == other.comments
            and self.less_term_matrix == other.less_term_matrix
            and self.greater_term_matrix == other.greater_term_matrix
            and self.equal_term_matrix == other.equal_term_matrix
            and self.group == other.group
            and self.filter_synthesis == other.filter_synthesis
            and self.filter_year_by_year == other.filter_year_by_year
        )

    def _create_diff(self, other: "ICommand") -> t.List["ICommand"]:
        from antarest.study.storage.variantstudy.model.command.update_binding_constraint import UpdateBindingConstraint

        other = t.cast(CreateBindingConstraint, other)
        bd_id = transform_name_to_id(self.name)

        args = {
            "id": bd_id,
            "enabled": other.enabled,
            "time_step": other.time_step,
            "operator": other.operator,
            "coeffs": other.coeffs,
            "filter_year_by_year": other.filter_year_by_year,
            "filter_synthesis": other.filter_synthesis,
            "comments": other.comments,
            "command_context": other.command_context,
            "group": other.group,
        }

        matrix_service = self.command_context.matrix_service
        for matrix_name in ["values", "less_term_matrix", "equal_term_matrix", "greater_term_matrix"]:
            self_matrix = getattr(self, matrix_name)  # matrix, ID or `None`
            other_matrix = getattr(other, matrix_name)  # matrix, ID or `None`
            self_matrix_id = None if self_matrix is None else matrix_service.get_matrix_id(self_matrix)
            other_matrix_id = None if other_matrix is None else matrix_service.get_matrix_id(other_matrix)
            if self_matrix_id != other_matrix_id:
                args[matrix_name] = other_matrix_id

        return [UpdateBindingConstraint(**args)]
