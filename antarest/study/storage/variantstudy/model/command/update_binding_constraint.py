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

from typing import Any, Dict, Mapping, Optional, Tuple

from typing_extensions import override

from antarest.core.model import JSON
from antarest.study.model import STUDY_VERSION_8_7
from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import (
    DEFAULT_GROUP,
    OPERATOR_MATRICES_MAP,
    BindingConstraintFrequency,
    BindingConstraintOperator,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import BindingConstraintDTO, FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.variantstudy.model.command.common import CommandName, CommandOutput
from antarest.study.storage.variantstudy.model.command.create_binding_constraint import (
    AbstractBindingConstraintCommand,
    TermMatrices,
    create_binding_constraint_props,
)
from antarest.study.storage.variantstudy.model.command.icommand import ICommand
from antarest.study.storage.variantstudy.model.command_listener.command_listener import ICommandListener
from antarest.study.storage.variantstudy.model.model import CommandDTO


def update_matrices_names(
    file_study: FileStudy,
    bc_id: str,
    existing_operator: BindingConstraintOperator,
    new_operator: BindingConstraintOperator,
) -> None:
    """
    Update the matrix file name according to the new operator.
    Due to legacy matrices generation, we need to check if the new matrix file already exists
    and if it does, we need to first remove it before renaming the existing matrix file

    Args:
        file_study: the file study
        bc_id: the binding constraint ID
        existing_operator: the existing operator
        new_operator: the new operator

    Raises:
        NotImplementedError: if the case is not handled
    """

    handled_operators = [
        BindingConstraintOperator.EQUAL,
        BindingConstraintOperator.LESS,
        BindingConstraintOperator.GREATER,
        BindingConstraintOperator.BOTH,
    ]

    if (existing_operator not in handled_operators) or (new_operator not in handled_operators):
        raise NotImplementedError(
            f"Case not handled yet: existing_operator={existing_operator}, new_operator={new_operator}"
        )
    elif existing_operator == new_operator:
        return  # nothing to do

    parent_folder_node = file_study.tree.get_node(["input", "bindingconstraints"])
    error_msg = "Unhandled node type, expected InputSeriesMatrix, got "
    if existing_operator != BindingConstraintOperator.BOTH and new_operator != BindingConstraintOperator.BOTH:
        current_node = parent_folder_node.get_node([f"{bc_id}_{OPERATOR_MATRICES_MAP[existing_operator][0]}"])
        assert isinstance(current_node, InputSeriesMatrix), f"{error_msg}{type(current_node)}"
        current_node.rename_file(f"{bc_id}_{OPERATOR_MATRICES_MAP[new_operator][0]}")
    elif new_operator == BindingConstraintOperator.BOTH:
        current_node = parent_folder_node.get_node([f"{bc_id}_{OPERATOR_MATRICES_MAP[existing_operator][0]}"])
        assert isinstance(current_node, InputSeriesMatrix), f"{error_msg}{type(current_node)}"
        if existing_operator == BindingConstraintOperator.EQUAL:
            current_node.copy_file(f"{bc_id}_gt")
            current_node.rename_file(f"{bc_id}_lt")
        else:
            term = "lt" if existing_operator == BindingConstraintOperator.GREATER else "gt"
            current_node.copy_file(f"{bc_id}_{term}")
    else:
        current_node = parent_folder_node.get_node([f"{bc_id}_lt"])
        assert isinstance(current_node, InputSeriesMatrix), f"{error_msg}{type(current_node)}"
        if new_operator == BindingConstraintOperator.GREATER:
            current_node.delete()
        else:
            parent_folder_node.get_node([f"{bc_id}_gt"]).delete()
            if new_operator == BindingConstraintOperator.EQUAL:
                current_node.rename_file(f"{bc_id}_eq")


class UpdateBindingConstraint(AbstractBindingConstraintCommand):
    """
    Command used to update a binding constraint.
    """

    # Overloaded metadata
    # ===================

    command_name: CommandName = CommandName.UPDATE_BINDING_CONSTRAINT

    # Command parameters
    # ==================

    # Properties of the `UPDATE_BINDING_CONSTRAINT` command:
    id: str

    @override
    def _apply_config(self, study_data: FileStudyTreeConfig) -> Tuple[CommandOutput, Dict[str, Any]]:
        index = next(i for i, bc in enumerate(study_data.bindings) if bc.id == self.id)
        existing_constraint = study_data.bindings[index]
        areas_set = existing_constraint.areas
        clusters_set = existing_constraint.clusters
        if self.coeffs:
            areas_set = set()
            clusters_set = set()
            for j in self.coeffs.keys():
                if "%" in j:
                    areas_set |= set(j.split("%"))
                elif "." in j:
                    clusters_set.add(j)
                    areas_set.add(j.split(".")[0])
        group = self.group or existing_constraint.group
        operator = self.operator or existing_constraint.operator
        time_step = self.time_step or existing_constraint.time_step
        new_constraint = BindingConstraintDTO(
            id=self.id,
            group=group,
            areas=areas_set,
            clusters=clusters_set,
            operator=operator,
            time_step=time_step,
        )
        study_data.bindings[index] = new_constraint
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

    @override
    def _apply(self, study_data: FileStudy, listener: Optional[ICommandListener] = None) -> CommandOutput:
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

        study_version = study_data.config.version
        # rename matrices if the operator has changed for version >= 870
        if self.operator and study_version >= STUDY_VERSION_8_7:
            existing_operator = BindingConstraintOperator(actual_cfg["operator"])
            new_operator = self.operator
            update_matrices_names(study_data, self.id, existing_operator, new_operator)

        self._apply_config(study_data.config)

        updated_matrices = [
            term for term in [m.value for m in TermMatrices] if hasattr(self, term) and getattr(self, term)
        ]

        time_step = self.time_step or BindingConstraintFrequency(actual_cfg["type"])
        self.validates_and_fills_matrices(
            time_step=time_step, specific_matrices=updated_matrices or None, version=study_version, create=False
        )

        props = create_binding_constraint_props(**self.model_dump())
        obj = props.model_dump(mode="json", by_alias=True, exclude_unset=True)

        updated_cfg = binding_constraints[index]
        updated_cfg.update(obj)

        excluded_fields = set(ICommand.model_fields) | {"id"}
        updated_properties = self.model_dump(exclude=excluded_fields, exclude_none=True)
        # This 2nd check is here to remove the last term.
        if self.coeffs or updated_properties == {"coeffs": {}}:
            # Remove terms which IDs contain a "%" or a "." in their name
            term_ids = {k for k in updated_cfg if "%" in k or "." in k}
            binding_constraints[index] = {k: v for k, v in updated_cfg.items() if k not in term_ids}

        return super().apply_binding_constraint(study_data, binding_constraints, index, self.id, old_groups=old_groups)

    @override
    def to_dto(self) -> CommandDTO:
        matrices = ["values"] + [m.value for m in TermMatrices]
        matrix_service = self.command_context.matrix_service

        excluded_fields = set(ICommand.model_fields)
        json_command = self.model_dump(mode="json", exclude=excluded_fields, exclude_none=True)
        for key in json_command:
            if key in matrices:
                json_command[key] = matrix_service.get_matrix_id(json_command[key])

        return CommandDTO(
            action=self.command_name.value, args=json_command, version=1, study_version=self.study_version
        )
