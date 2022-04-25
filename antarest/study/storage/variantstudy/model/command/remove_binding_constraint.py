import logging
from typing import Any, List, Tuple, Dict

from antarest.core.model import JSON
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    transform_name_to_id,
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import (
    CommandOutput,
    CommandName,
)
from antarest.study.storage.variantstudy.model.command.icommand import (
    ICommand,
    MATCH_SIGNATURE_SEPARATOR,
)
from antarest.study.storage.variantstudy.model.model import CommandDTO


class RemoveBindingConstraint(ICommand):
    id: str

    def __init__(self, **data: Any) -> None:
        super().__init__(
            command_name=CommandName.REMOVE_BINDING_CONSTRAINT,
            version=1,
            **data,
        )

    def _apply_config(
        self, study_data: FileStudyTreeConfig
    ) -> Tuple[CommandOutput, Dict[str, Any]]:
        if self.id not in study_data.bindings:
            return (
                CommandOutput(
                    status=False, message="Binding constraint not found"
                ),
                dict(),
            )
        study_data.bindings.remove(self.id)
        return CommandOutput(status=True), dict()

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
        return str(
            self.command_name.value + MATCH_SIGNATURE_SEPARATOR + self.id
        )

    def match(self, other: ICommand, equal: bool = False) -> bool:
        if not isinstance(other, RemoveBindingConstraint):
            return False
        return self.id == other.id

    def revert(
        self, history: List["ICommand"], base: FileStudy
    ) -> List["ICommand"]:
        from antarest.study.storage.variantstudy.model.command.create_binding_constraint import (
            CreateBindingConstraint,
        )
        from antarest.study.storage.variantstudy.model.command.utils_extractor import (
            CommandExtraction,
        )

        for command in reversed(history):
            if (
                isinstance(command, CreateBindingConstraint)
                and transform_name_to_id(command.name) == self.id
            ):
                return [command]

        try:
            return (
                CommandExtraction(
                    self.command_context.matrix_service,
                    self.command_context.patch_service,
                )
            ).extract_binding_constraint(base, self.id)
        except Exception as e:
            logging.getLogger(__name__).warning(
                f"Failed to extract revert command for remove_binding_constraint {self.id}",
                exc_info=e,
            )
            return []

    def _create_diff(self, other: "ICommand") -> List["ICommand"]:
        return []

    def get_inner_matrices(self) -> List[str]:
        return []
