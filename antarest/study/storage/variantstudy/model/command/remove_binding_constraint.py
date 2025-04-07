# Copyright (c) 2025, RTE (https://www.rte-france.com)
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

from typing import Any, Dict, List, Optional, Tuple

from typing_extensions import override

from antarest.core.model import JSON
from antarest.study.model import STUDY_VERSION_8_7
from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import DEFAULT_GROUP
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.binding_constraint_utils import remove_bc_from_scenario_builder
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class RemoveBindingConstraint(ICommand):
    """
    Command used to remove a binding constraint.
    """

    command_name: CommandName = CommandName.REMOVE_BINDING_CONSTRAINT

    # Properties of the `REMOVE_BINDING_CONSTRAINT` command:
    id: str

    @override
    def _apply_config(self, study_data: FileStudyTreeConfig) -> Tuple[CommandOutput, Dict[str, Any]]:  # type: ignore
        pass  # TODO DELETE

    def remove_from_config(self, study_data: FileStudyTreeConfig) -> CommandOutput:
        if self.id not in [bind.id for bind in study_data.bindings]:
            return CommandOutput(status=False, message="Binding constraint not found")
        study_data.bindings.remove(next(iter([bind for bind in study_data.bindings if bind.id == self.id])))
        return CommandOutput(status=True)

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
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
        if study_data.config.version < STUDY_VERSION_8_7:
            study_data.tree.delete(["input", "bindingconstraints", self.id])
        else:
            existing_files = study_data.tree.get(["input", "bindingconstraints"], depth=1)
            for term in ["lt", "gt", "eq"]:
                matrix_id = f"{self.id}_{term}"
                if matrix_id in existing_files:
                    study_data.tree.delete(["input", "bindingconstraints", matrix_id])

            # When all BC of a given group are removed, the group should be removed from the scenario builder
            old_groups = {bd.get("group", DEFAULT_GROUP).lower() for bd in binding_constraints.values()}
            new_groups = {bd.get("group", DEFAULT_GROUP).lower() for bd in new_binding_constraints.values()}
            removed_groups = old_groups - new_groups
            remove_bc_from_scenario_builder(study_data, removed_groups)

        return self.remove_from_config(study_data.config)

    @override
    def to_dto(self) -> CommandDTO:
        return CommandDTO(
            action=CommandName.REMOVE_BINDING_CONSTRAINT.value,
            args={
                "id": self.id,
            },
            study_version=self.study_version,
        )

    @override
    def get_inner_matrices(self) -> List[str]:
        return []
