# Copyright (c) 2024, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.
import typing as t

from typing_extensions import override

from antarest.study.model import STUDY_VERSION_8_7
from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import DEFAULT_GROUP
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import MATCH_SIGNATURE_SEPARATOR, ICommand, OutputTuple
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class RemoveMultipleBindingConstraints(ICommand):
    """
    Command used to remove multiple binding constraints at once.
    """

    command_name: CommandName = CommandName.REMOVE_MULTIPLE_BINDING_CONSTRAINTS
    version: int = 1

    # Properties of the `REMOVE_MULTIPLE_BINDING_CONSTRAINT` command:
    ids: t.List[str]

    @override
    def _apply_config(self, study_data: FileStudyTreeConfig) -> OutputTuple:
        return CommandOutput(status=True), {}

    @override
    def _apply(self, study_data: FileStudy, listener: t.Optional[ICommandListener] = None) -> CommandOutput:
        # If at least one bc is missing in the database, we raise an error
        already_existing_ids = {obj.id for obj in study_data.config.bindings}
        missing_ids = [id_ for id_ in self.ids if id_ not in already_existing_ids]
        if len(missing_ids) > 0:
            return CommandOutput(status=False, message=f"Binding constraint not found: '{missing_ids}'")

        binding_constraints = study_data.tree.get(["input", "bindingconstraints", "bindingconstraints"])

        old_groups = {bd.get("group", DEFAULT_GROUP).lower() for bd in binding_constraints.values()}

        deleted_binding_constraints = {}

        for key in list(binding_constraints.keys()):
            if binding_constraints[key].get("id") in self.ids:
                deleted_binding_constraints[key] = binding_constraints.pop(key)

        study_data.tree.save(
            binding_constraints,
            ["input", "bindingconstraints", "bindingconstraints"],
        )

        for bc in deleted_binding_constraints:
            if study_data.config.version < STUDY_VERSION_8_7:
                study_data.tree.delete(["input", "bindingconstraints", deleted_binding_constraints[bc].get("id")])
            else:
                existing_files = study_data.tree.get(["input", "bindingconstraints"], depth=1)
                for term in ["lt", "gt", "eq"]:
                    matrix_id = f"{deleted_binding_constraints[bc].get('id')}_{term}"
                    if matrix_id in existing_files:
                        study_data.tree.delete(["input", "bindingconstraints", matrix_id])

        new_groups = {bd.get("group", DEFAULT_GROUP).lower() for bd in binding_constraints.values()}
        removed_groups = old_groups - new_groups
        self.remove_bc_from_scenario_builder(study_data, removed_groups)

        return self._apply_config(study_data.config)[0]

    def remove_bc_from_scenario_builder(self, study_data: FileStudy, removed_groups: t.Set[str]) -> None:
        """
        Update the scenario builder by removing the rows that correspond to the BC groups to remove.

        NOTE: this update can be very long if the scenario builder configuration is large.
        """
        if not removed_groups:
            return

        rulesets = study_data.tree.get(["settings", "scenariobuilder"])

        for ruleset in rulesets.values():
            for key in list(ruleset):
                # The key is in the form "symbol,group,year"
                symbol, *parts = key.split(",")
                if symbol == "bc" and parts[0] in removed_groups:
                    del ruleset[key]

        study_data.tree.save(rulesets, ["settings", "scenariobuilder"])

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.REMOVE_MULTIPLE_BINDING_CONSTRAINTS.value,
            args={
                "ids": self.ids,
            },
            study_version=self.study_version,
        )

    @override
    def match_signature(self) -> str:
        return str(self.command_name.value + MATCH_SIGNATURE_SEPARATOR + ",".join(self.ids))

    @override
    def match(self, other: ICommand, equal: bool = False) -> bool:
        if not isinstance(other, RemoveMultipleBindingConstraints):
            return False
        return self.ids == other.ids

    @override
    def _create_diff(self, other: "ICommand") -> t.List["ICommand"]:
        return []

    @override
    def get_inner_matrices(self) -> t.List[str]:
        return []
