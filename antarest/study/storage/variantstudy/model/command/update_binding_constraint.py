import json
from typing import Any, Dict, List, Optional, Tuple

from antarest.core.model import JSON
from antarest.matrixstore.model import MatrixData
from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import BindingConstraintFrequency
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.create_binding_constraint import (
    TERM_MATRICES,
    AbstractBindingConstraintCommand,
)
from antarest.study.storage.variantstudy.model.command.icommand import MATCH_SIGNATURE_SEPARATOR, ICommand
from antarest.study.storage.variantstudy.model.model import CommandDTO

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
        existing_key: Optional[str] = None
        for key, binding_config in binding_constraints.items():
            if binding_config["id"] == self.id:
                binding = binding_config
                existing_key = key
                break
        if binding is None or existing_key is None:
            return CommandOutput(
                status=False,
                message="Failed to retrieve existing binding constraint",
            )

        updated_matrices = [term for term in TERM_MATRICES if hasattr(self, term) and getattr(self, term)]
        study_version = study_data.config.version
        time_step = self.time_step or BindingConstraintFrequency(binding.get("type"))
        self.validates_and_fills_matrices(
            time_step=time_step, specific_matrices=updated_matrices or None, version=study_version, create=False
        )

        include = {"enabled", "time_step", "operator", "comments"}
        if study_version >= 830:
            include |= {"filter_year_by_year", "filter_synthesis"}
        if study_version >= 870:
            include |= {"group"}

        obj = json.loads(self.json(by_alias=True, include=include, exclude_none=True))
        existing_constraint = binding_constraints[str(existing_key)]
        existing_constraint.update(obj)

        if self.coeffs:
            # We want to remove existing coeffs to replace them.
            allowed_keys = {
                "name": existing_constraint["name"],
                # fixme: [review] we must exclude ICommand.__fields__ names, not only command_context
                **json.loads(self.json(exclude={"command_context"}, by_alias=True)),
            }
            keys_to_delete = [key for key in existing_constraint if key not in allowed_keys]
            for key in keys_to_delete:
                del existing_constraint[key]

        return super().apply_binding_constraint(study_data, binding_constraints, existing_key, self.id)

    def to_dto(self) -> CommandDTO:
        matrices = ["values"] + TERM_MATRICES
        matrix_service = self.command_context.matrix_service
        json_command = json.loads(
            self.json(exclude={"command_context", "command_id", "command_name", "version"}, exclude_none=True)
        )
        for key in json_command:
            if key in matrices:
                json_command[key] = matrix_service.get_matrix_id(json_command[key])

        return CommandDTO(action=self.command_name.value, args=json_command, version=self.version)

    def match_signature(self) -> str:
        return str(self.command_name.value + MATCH_SIGNATURE_SEPARATOR + self.id)

    def _create_diff(self, other: "ICommand") -> List["ICommand"]:
        return [other]
