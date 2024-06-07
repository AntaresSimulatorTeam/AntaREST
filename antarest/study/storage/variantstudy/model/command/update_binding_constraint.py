import json
from typing import Any, Dict, List, Mapping, Optional, Tuple

from antarest.core.model import JSON
from antarest.matrixstore.model import MatrixData
from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import BindingConstraintFrequency
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.create_binding_constraint import (
    DEFAULT_GROUP,
    TERM_MATRICES,
    AbstractBindingConstraintCommand,
    create_binding_constraint_config,
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

    def _find_binding_config(self, binding_constraints: Mapping[str, JSON]) -> Optional[Tuple[str, JSON]]:
        """
        Find the binding constraint with the given ID in the list of binding constraints,
        and returns its index and configuration, or `None` if it does not exist.
        """
        for index, binding_config in binding_constraints.items():
            if binding_config["id"] == self.id:
                # convert to string because the index could be an integer
                return str(index), binding_config
        return None

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        binding_constraints = study_data.tree.get(["input", "bindingconstraints", "bindingconstraints"])

        # When all BC of a given group are removed, the group should be removed from the scenario builder
        old_groups = {bd.get("group", DEFAULT_GROUP).lower() for bd in binding_constraints.values()}

        index_and_cfg = self._find_binding_config(binding_constraints)
        if index_and_cfg is None:
            return CommandOutput(
                status=False,
                message="The binding constraint with ID '{self.id}' does not exist",
            )

        index, actual_cfg = index_and_cfg

        updated_matrices = [term for term in TERM_MATRICES if hasattr(self, term) and getattr(self, term)]
        study_version = study_data.config.version
        time_step = self.time_step or BindingConstraintFrequency(actual_cfg.get("type"))
        self.validates_and_fills_matrices(
            time_step=time_step, specific_matrices=updated_matrices or None, version=study_version, create=False
        )

        study_version = study_data.config.version
        props = create_binding_constraint_config(study_version, **self.dict())
        obj = json.loads(props.json(by_alias=True, exclude_unset=True))

        updated_cfg = binding_constraints[index]
        updated_cfg.update(obj)

        updated_terms = set(self.coeffs.keys()) if self.coeffs else set()

        # Remove the terms not in the current update but existing in the config
        terms_to_remove = {key for key in updated_cfg if ("%" in key or "." in key) and key not in updated_terms}
        for term_id in terms_to_remove:
            updated_cfg.pop(term_id, None)

        return super().apply_binding_constraint(study_data, binding_constraints, index, self.id, old_groups=old_groups)

    def to_dto(self) -> CommandDTO:
        matrices = ["values"] + TERM_MATRICES
        matrix_service = self.command_context.matrix_service

        excluded_fields = frozenset(ICommand.__fields__)
        json_command = json.loads(self.json(exclude=excluded_fields, exclude_none=True))
        for key in json_command:
            if key in matrices:
                json_command[key] = matrix_service.get_matrix_id(json_command[key])

        return CommandDTO(action=self.command_name.value, args=json_command, version=self.version)

    def match_signature(self) -> str:
        return str(self.command_name.value + MATCH_SIGNATURE_SEPARATOR + self.id)

    def _create_diff(self, other: "ICommand") -> List["ICommand"]:
        return [other]

    def match(self, other: "ICommand", equal: bool = False) -> bool:
        if not isinstance(other, self.__class__):
            return False
        if not equal:
            return self.id == other.id
        return super().match(other, equal)
