import typing
from typing import Any, Dict, List, Tuple

from antarest.core.model import JSON
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.create_binding_constraint import DEFAULT_GROUP
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
        return CommandOutput(status=True), {}

    # noinspection PyMethodMayBeStatic
    def _remove_bc_from_scenario_builder(self, study_data: FileStudy, removed_groups: typing.Set[str]) -> None:
        """
        Update the scenario builder by removing the rows that correspond to the BC groups to remove.

        NOTE: this update can be very long if the scenario builder configuration is large.
        """
        rulesets = study_data.tree.get(["settings", "scenariobuilder"])

        for ruleset in rulesets.values():
            for key in list(ruleset):
                # The key is in the form "symbol,group,year"
                symbol, *parts = key.split(",")
                if symbol == "bc" and parts[0] in removed_groups:
                    del ruleset[key]

        study_data.tree.save(rulesets, ["settings", "scenariobuilder"])

    def _apply(self, study_data: FileStudy) -> CommandOutput:
        if self.id not in [bind.id for bind in study_data.config.bindings]:
            return CommandOutput(status=False, message=f"Binding constraint not found: '{self.id}'")
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

            # When all BC of a given group are removed, the group should be removed from the scenario builder
            old_groups = {bd.get("group", DEFAULT_GROUP).lower() for bd in binding_constraints.values()}
            new_groups = {bd.get("group", DEFAULT_GROUP).lower() for bd in new_binding_constraints.values()}
            removed_groups = old_groups - new_groups
            self._remove_bc_from_scenario_builder(study_data, removed_groups)

        return self._apply_config(study_data.config)[0]

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
