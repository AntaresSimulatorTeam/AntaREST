from typing import Any, Dict, List, Optional, Tuple

from antarest.core.model import JSON
from antarest.matrixstore.model import MatrixData
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.business.utils_binding_constraint import apply_binding_constraint
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.create_binding_constraint import AbstractBindingConstraintCommand
from antarest.study.storage.variantstudy.model.command.icommand import MATCH_SIGNATURE_SEPARATOR, ICommand
from antarest.study.storage.variantstudy.model.model import CommandDTO

__all__ = ("UpdateBindingConstraint",)

MatrixType = List[List[MatrixData]]


class UpdateBindingConstraint(AbstractBindingConstraintCommand):
    """
    Command used to update a binding constraint.
    """

    # Overloaded metadata
    # ===================

    command_name = CommandName.UPDATE_BINDING_CONSTRAINT
    version: int = 1

    # Command parameters
    # ==================

    # Properties of the `UPDATE_BINDING_CONSTRAINT` command:
    id: str

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

        # fmt: off
        updated_matrices = [term for term in ["less_term_matrix", "equal_term_matrix", "greater_term_matrix"] if self.__getattribute__(term)]
        self.validates_and_fills_matrices(specific_matrices=updated_matrices or None, version=study_data.config.version, create=False)
        # fmt: on

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
            self.less_term_matrix,
            self.greater_term_matrix,
            self.equal_term_matrix,
            self.filter_year_by_year,
            self.filter_synthesis,
            self.group,
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
            and self.less_term_matrix == other.less_term_matrix
            and self.greater_term_matrix == other.greater_term_matrix
            and self.equal_term_matrix == other.equal_term_matrix
            and self.comments == other.comments
            and self.group == other.group
            and self.filter_synthesis == other.filter_synthesis
            and self.filter_year_by_year == other.filter_year_by_year
        )

    def _create_diff(self, other: "ICommand") -> List["ICommand"]:
        return [other]
