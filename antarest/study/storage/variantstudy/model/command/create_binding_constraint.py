from abc import ABCMeta
from typing import Any, Dict, List, Optional, Tuple, Union, cast

import numpy as np
from pydantic import Field, validator

from antarest.matrixstore.model import MatrixData
from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import BindingConstraintFrequency
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig, transform_name_to_id
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.matrix_constants_generator import GeneratorMatrixConstants
from antarest.study.storage.variantstudy.business.utils import strip_matrix_protocol, validate_matrix
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

__all__ = ("AbstractBindingConstraintCommand", "CreateBindingConstraint", "check_matrix_values")

MatrixType = List[List[MatrixData]]


def check_matrix_values(time_step: BindingConstraintFrequency, values: MatrixType) -> None:
    """
    Check the binding constraint's matrix values for the specified time step.

    Args:
        time_step: The frequency of the binding constraint: "hourly", "daily" or "weekly".
        values: The binding constraint's 2nd member matrix.

    Raises:
        ValueError:
            If the matrix shape does not match the expected shape for the given time step.
            If the matrix values contain NaN (Not-a-Number).
    """
    shapes = {
        BindingConstraintFrequency.HOURLY: (8760, 3),
        BindingConstraintFrequency.DAILY: (365, 3),
        BindingConstraintFrequency.WEEKLY: (52, 3),
    }
    # Check the matrix values and create the corresponding matrix link
    array = np.array(values, dtype=np.float64)
    if array.shape != shapes[time_step]:
        raise ValueError(f"Invalid matrix shape {array.shape}, expected {shapes[time_step]}")
    if np.isnan(array).any():
        raise ValueError("Matrix values cannot contain NaN")


class AbstractBindingConstraintCommand(ICommand, metaclass=ABCMeta):
    """
    Abstract class for binding constraint commands.
    """

    # todo: add the `name` attribute because it should also be updated
    enabled: bool = True
    time_step: BindingConstraintFrequency
    operator: BindingConstraintOperator
    coeffs: Dict[str, List[float]]
    values: Optional[Union[MatrixType, str]] = Field(None, description="2nd member matrix")
    filter_year_by_year: Optional[str] = None
    filter_synthesis: Optional[str] = None
    comments: Optional[str] = None

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
        if self.values is not None:
            args["values"] = strip_matrix_protocol(self.values)
        return CommandDTO(
            action=self.command_name.value,
            args=args,
        )

    def get_inner_matrices(self) -> List[str]:
        if self.values is not None:
            if not isinstance(self.values, str):  # pragma: no cover
                raise TypeError(repr(self.values))
            return [strip_matrix_protocol(self.values)]
        return []


class CreateBindingConstraint(AbstractBindingConstraintCommand):
    """
    Command used to create a binding constraint.
    """

    command_name = CommandName.CREATE_BINDING_CONSTRAINT
    version: int = 1

    # Properties of the `CREATE_BINDING_CONSTRAINT` command:
    name: str

    @validator("values", always=True)
    def validate_series(
        cls,
        v: Optional[Union[MatrixType, str]],
        values: Dict[str, Any],
    ) -> Optional[Union[MatrixType, str]]:
        constants: GeneratorMatrixConstants
        constants = values["command_context"].generator_matrix_constants
        time_step = values["time_step"]
        if v is None:
            # Use an already-registered default matrix
            methods = {
                BindingConstraintFrequency.HOURLY: constants.get_binding_constraint_hourly,
                BindingConstraintFrequency.DAILY: constants.get_binding_constraint_daily,
                BindingConstraintFrequency.WEEKLY: constants.get_binding_constraint_weekly,
            }
            method = methods[time_step]
            return method()
        if isinstance(v, str):
            # Check the matrix link
            return validate_matrix(v, values)
        if isinstance(v, list):
            check_matrix_values(time_step, v)
            return validate_matrix(v, values)
        # Invalid datatype
        # pragma: no cover
        raise TypeError(repr(v))

    def _apply_config(self, study_data_config: FileStudyTreeConfig) -> Tuple[CommandOutput, Dict[str, Any]]:
        bd_id = transform_name_to_id(self.name)
        parse_bindings_coeffs_and_save_into_config(bd_id, study_data_config, self.coeffs)
        return CommandOutput(status=True), {}

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        binding_constraints = study_data.tree.get(["input", "bindingconstraints", "bindingconstraints"])
        new_key = len(binding_constraints)
        bd_id = transform_name_to_id(self.name)
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
            self.filter_year_by_year,
            self.filter_synthesis,
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
        )

    def _create_diff(self, other: "ICommand") -> List["ICommand"]:
        other = cast(CreateBindingConstraint, other)
        from antarest.study.storage.variantstudy.model.command.update_binding_constraint import UpdateBindingConstraint

        bd_id = transform_name_to_id(self.name)
        return [
            UpdateBindingConstraint(
                id=bd_id,
                enabled=other.enabled,
                time_step=other.time_step,
                operator=other.operator,
                coeffs=other.coeffs,
                values=strip_matrix_protocol(other.values) if self.values != other.values else None,
                filter_year_by_year=other.filter_year_by_year,
                filter_synthesis=other.filter_synthesis,
                comments=other.comments,
                command_context=other.command_context,
            )
        ]
