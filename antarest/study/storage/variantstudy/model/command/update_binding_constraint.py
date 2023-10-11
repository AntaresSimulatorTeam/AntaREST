from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import validator

from antarest.core.model import JSON
from antarest.matrixstore.model import MatrixData
from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import BindingConstraintFrequency
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.utils import validate_matrix
from antarest.study.storage.variantstudy.business.utils_binding_constraint import apply_binding_constraint
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.create_binding_constraint import (
    AbstractBindingConstraintCommand,
    check_matrix_values,
)
from antarest.study.storage.variantstudy.model.command.icommand import MATCH_SIGNATURE_SEPARATOR, ICommand
from antarest.study.storage.variantstudy.model.model import CommandDTO

__all__ = ("UpdateBindingConstraint",)

MatrixType = List[List[MatrixData]]


class UpdateBindingConstraint(AbstractBindingConstraintCommand):
    """
    Command used to update a binding constraint.
    """

    command_name: CommandName = CommandName.UPDATE_BINDING_CONSTRAINT
    version: int = 1

    # Properties of the `UPDATE_BINDING_CONSTRAINT` command:
    id: str

    @validator("values", always=True)
    def validate_series(
        cls,
        v: Optional[Union[MatrixType, str]],
        values: Dict[str, Any],
    ) -> Optional[Union[MatrixType, str]]:
        time_step = values["time_step"]
        if v is None:
            # The matrix is not updated
            return None
        if isinstance(v, str):
            # Check the matrix link
            return validate_matrix(v, values)
        if isinstance(v, list):
            check_matrix_values(time_step, v)
            return validate_matrix(v, values)
        # Invalid datatype
        # pragma: no cover
        raise TypeError(repr(v))

    def _apply_config(self, study_data: FileStudyTreeConfig) -> Tuple[CommandOutput, Dict[str, Any]]:
        return CommandOutput(status=True), {}

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        binding_constraints = study_data.tree.get(["input", "bindingconstraints", "bindingconstraints"])

        binding: Optional[JSON] = None
        new_key: Optional[str] = None
        for key, binding_config in binding_constraints.items():
            if binding_config["id"] == self.id:
                binding = binding_config
                new_key = key
                break
        if binding is None or new_key is None:
            return CommandOutput(
                status=False,
                message="Failed to retrieve existing binding constraint",
            )

        return apply_binding_constraint(
            study_data,
            binding_constraints,
            new_key,
            self.id,
            binding["name"],
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
        dto.args["id"] = self.id  # type: ignore
        return dto

    def match_signature(self) -> str:
        return str(self.command_name.value + MATCH_SIGNATURE_SEPARATOR + self.id)

    def match(self, other: ICommand, equal: bool = False) -> bool:
        if not isinstance(other, UpdateBindingConstraint):
            return False
        simple_match = self.id == other.id
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
        return [other]
