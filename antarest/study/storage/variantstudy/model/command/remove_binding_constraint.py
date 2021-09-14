from typing import Any

from antarest.core.custom_types import JSON
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.model import CommandDTO
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand


class RemoveBindingConstraint(ICommand):
    id: str

    def __init__(self, **data: Any) -> None:
        super().__init__(
            command_name=CommandName.REMOVE_BINDING_CONSTRAINT,
            version=1,
            **data,
        )

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        if self.id not in study_data.config.bindings:
            return CommandOutput(
                status=False, message="Binding constraint not found"
            )

        binding_constraints = study_data.tree.get(
            ["input", "bindingconstraints", "bindingconstraints"]
        )
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
        study_data.tree.delete(["input", "bindingconstraints", self.id])
        study_data.config.bindings.remove(self.id)
        return CommandOutput(status=True)

    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.REMOVE_BINDING_CONSTRAINT.value,
            args={
                "id": self.id,
            },
        )
