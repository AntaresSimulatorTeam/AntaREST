from typing import Any, Dict, List, Tuple

from antarest.core.model import JSON
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import MATCH_SIGNATURE_SEPARATOR, ICommand
from antarest.study.storage.variantstudy.model.model import CommandDTO


class RemoveBindingConstraint(ICommand):
    """
    Command used to remove a binding constraint.
    """

    command_name = CommandName.REMOVE_BINDING_CONSTRAINT
    version: int = 1

    # Properties of the `REMOVE_BINDING_CONSTRAINT` command:
    id: str

    def _apply_config(self, study_data: FileStudyTreeConfig) -> Tuple[CommandOutput, Dict[str, Any]]:
        if self.id not in [bind.id for bind in study_data.bindings]:
            return (
                CommandOutput(status=False, message="Binding constraint not found"),
                dict(),
            )
        study_data.bindings.remove(next(iter([bind for bind in study_data.bindings if bind.id == self.id])))
        return CommandOutput(status=True), dict()

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        if self.id not in [bind.id for bind in study_data.config.bindings]:
            return CommandOutput(status=False, message="Binding constraint not found")
        binding_constraints = study_data.tree.get(["input", "bindingconstraints", "bindingconstraints"])
        new_binding_constraints: JSON = {}
        index = 0
        for bd in binding_constraints:
            if binding_constraints[bd]["id"] == self.id:
                continue
            new_binding_constraints[str(index)] = binding_constraints[bd]
            index += 1
        study_data.tree.save(
            new_binding_constraints,
            ["input", "bindingconstraints", "bindingconstraints"],
        )
        if study_data.config.version < 870:
            study_data.tree.delete(["input", "bindingconstraints", self.id])
        else:
            for term in ["lt", "gt", "eq"]:
                study_data.tree.delete(["input", "bindingconstraints", f"{self.id}_{term}"])
        output, _ = self._apply_config(study_data.config)
        return output

    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.REMOVE_BINDING_CONSTRAINT.value,
            args={
                "id": self.id,
            },
        )

    def match_signature(self) -> str:
        return str(self.command_name.value + MATCH_SIGNATURE_SEPARATOR + self.id)

    def match(self, other: ICommand, equal: bool = False) -> bool:
        if not isinstance(other, RemoveBindingConstraint):
            return False
        return self.id == other.id

    def _create_diff(self, other: "ICommand") -> List["ICommand"]:
        return []

    def get_inner_matrices(self) -> List[str]:
        return []
