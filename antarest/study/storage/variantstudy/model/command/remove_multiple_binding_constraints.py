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

from typing import List, Optional

from typing_extensions import override

from antarest.study.model import STUDY_VERSION_8_7
from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import DEFAULT_GROUP
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.variantstudy.model.command.binding_constraint_utils import remove_bc_from_scenario_builder
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


class RemoveMultipleBindingConstraints(ICommand):
    """
    Command used to remove multiple binding constraints at once.
    """

    command_name: CommandName = CommandName.REMOVE_MULTIPLE_BINDING_CONSTRAINTS

    # Properties of the `REMOVE_MULTIPLE_BINDING_CONSTRAINTS` command:
    ids: List[str]

    def remove_from_config(self, study_data: FileStudyTreeConfig) -> CommandOutput:
        # If at least one bc is missing in the database, we raise an error
        already_existing_ids = {binding.id for binding in study_data.bindings}
        missing_bc_ids = [id_ for id_ in self.ids if id_ not in already_existing_ids]

        if missing_bc_ids:
            return CommandOutput(status=False, message=f"Binding constraints missing: {missing_bc_ids}")

        return CommandOutput(status=True)

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
        command_output = self.remove_from_config(study_data.config)

        if not command_output.status:
            return command_output

        binding_constraints = study_data.tree.get(["input", "bindingconstraints", "bindingconstraints"])

        old_groups = {bd.get("group", DEFAULT_GROUP).lower() for bd in binding_constraints.values()}

        deleted_binding_constraints = []

        for key in list(binding_constraints.keys()):
            if binding_constraints[key].get("id") in self.ids:
                deleted_binding_constraints.append(binding_constraints.pop(key))

        # BC dict should start at index 0
        new_binding_constraints = {str(i): value for i, value in enumerate(binding_constraints.values())}

        study_data.tree.save(
            new_binding_constraints,
            ["input", "bindingconstraints", "bindingconstraints"],
        )

        existing_files = study_data.tree.get(["input", "bindingconstraints"], depth=1)
        for bc in deleted_binding_constraints:
            if study_data.config.version < STUDY_VERSION_8_7:
                study_data.tree.delete(["input", "bindingconstraints", bc.get("id")])
            else:
                for term in ["lt", "gt", "eq"]:
                    matrix_id = f"{bc.get('id')}_{term}"
                    if matrix_id in existing_files:
                        study_data.tree.delete(["input", "bindingconstraints", matrix_id])

        new_groups = {bd.get("group", DEFAULT_GROUP).lower() for bd in binding_constraints.values()}
        removed_groups = old_groups - new_groups
        remove_bc_from_scenario_builder(study_data, removed_groups)

        return command_output

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
    def get_inner_matrices(self) -> List[str]:
        return []
