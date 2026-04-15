# Copyright (c) 2026, RTE (https://www.rte-france.com)
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
from abc import ABC, abstractmethod
from collections.abc import Iterator, Sequence
from typing import TYPE_CHECKING, Any, Callable

import polars as pl
from antares.study.version import StudyVersion
from typing_extensions import override

from antarest.core.exceptions import BindingConstraintNotFound
from antarest.matrixstore.matrix_uri_mapper import extract_matrix_id
from antarest.study.business.model.binding_constraint_model import (
    OPERATOR_MATRICES_MAP,
    OPERATOR_MATRIX_FILE_MAP,
    BindingConstraint,
    BindingConstraintOperator,
    ConstraintId,
)
from antarest.study.dao.api.binding_constraint_dao import ConstraintDao
from antarest.study.dao.common import BindingConstraintSeriesMapping
from antarest.study.model import STUDY_VERSION_8_7
from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import (
    parse_binding_constraint,
    serialize_binding_constraint,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixNode

if TYPE_CHECKING:
    from antarest.study.dao.file.file_study_dao import FileStudyTreeDao


def _get_values_matrix_path(constraint_id: ConstraintId) -> list[str]:
    return ["input", "bindingconstraints", constraint_id]


def _get_less_term_matrix_path(constraint_id: ConstraintId) -> list[str]:
    return ["input", "bindingconstraints", f"{constraint_id}_lt"]


def _get_greater_term_matrix_path(constraint_id: ConstraintId) -> list[str]:
    return ["input", "bindingconstraints", f"{constraint_id}_gt"]


def _get_equal_term_matrix_path(constraint_id: ConstraintId) -> list[str]:
    return ["input", "bindingconstraints", f"{constraint_id}_eq"]


def get_next_available_key(ini_content: dict[str, Any]) -> str:
    """Find the next available key in the ini content."""
    existing_keys = {int(k) for k in ini_content.keys() if k.isdigit()}
    next_key = 0
    while next_key in existing_keys:
        next_key += 1
    return str(next_key)


def _get_constraint_id_from_matrix_file_name(filename: str, term: str | None = None) -> str | None:
    if not term:
        # Means we're before the v8.7
        return filename
    if filename.endswith(f"_{term}"):
        return filename.removesuffix(f"_{term}")
    return None


class FileStudyConstraintDao(ConstraintDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @abstractmethod
    def get_impl(self) -> "FileStudyTreeDao":
        pass

    @override
    def get_all_constraints(self) -> dict[ConstraintId, BindingConstraint]:
        file_study = self.get_file_study()
        version = file_study.config.version
        config = _get_all_constraints_ini(file_study)

        constraints_by_id: dict[ConstraintId, BindingConstraint] = {}

        for constraint_ini in config.values():
            constraint = parse_binding_constraint(version, constraint_ini)
            constraints_by_id[constraint.id] = constraint
        return constraints_by_id

    @override
    def get_constraint(self, constraint_id: ConstraintId) -> BindingConstraint:
        result = self.get_all_constraints()
        if constraint_id not in result:
            raise BindingConstraintNotFound(f"Constraint {constraint_id} not found")
        return result[constraint_id]

    @override
    def get_constraint_values_matrix(self, constraint_id: ConstraintId) -> pl.DataFrame:
        return self.get_impl().get_matrix(_get_values_matrix_path(constraint_id))

    @override
    def get_constraint_less_term_matrix(self, constraint_id: ConstraintId) -> pl.DataFrame:
        return self.get_impl().get_matrix(_get_less_term_matrix_path(constraint_id))

    @override
    def get_constraint_greater_term_matrix(self, constraint_id: ConstraintId) -> pl.DataFrame:
        return self.get_impl().get_matrix(_get_greater_term_matrix_path(constraint_id))

    @override
    def get_constraint_equal_term_matrix(self, constraint_id: ConstraintId) -> pl.DataFrame:
        return self.get_impl().get_matrix(_get_equal_term_matrix_path(constraint_id))

    @override
    def get_all_constraint_values_matrix(self) -> BindingConstraintSeriesMapping:
        return self._get_all_bc_matrices()

    @override
    def get_all_constraint_less_term_matrix(self) -> BindingConstraintSeriesMapping:
        return self._get_all_bc_matrices("lt")

    @override
    def get_all_constraint_greater_term_matrix(self) -> BindingConstraintSeriesMapping:
        return self._get_all_bc_matrices("gt")

    @override
    def get_all_constraint_equal_term_matrix(self) -> BindingConstraintSeriesMapping:
        return self._get_all_bc_matrices("eq")

    @override
    def save_constraints(self, constraints: Sequence[BindingConstraint]) -> None:
        """This method can be called to save new constraints or to update existing ones."""
        study_data = self.get_file_study()
        study_version = study_data.config.version
        ini_content = _get_all_constraints_ini(study_data)

        bc_id_to_key_in_ini: dict[str, str] = {}
        bc_id_to_bc_object: dict[ConstraintId, BindingConstraint] = {}
        old_groups: dict[str, list[str]] = {}
        for key, bc in ini_content.items():
            constraint = parse_binding_constraint(study_data.config.version, bc)
            bc_id_to_key_in_ini[constraint.id] = key
            bc_id_to_bc_object[constraint.id] = constraint
            if constraint.group:
                old_groups.setdefault(constraint.group, []).append(constraint.id)

        existing_bindings = {bc.id: k for k, bc in enumerate(study_data.config.bindings)}

        for constraint in constraints:
            if constraint.id in bc_id_to_bc_object:
                # We're updating an existing constraint
                bc_id = constraint.id
                existing_constraint = bc_id_to_bc_object[bc_id]

                if study_version >= STUDY_VERSION_8_7 and (constraint.operator != existing_constraint.operator):
                    # The user changed the operator, we have to rename matrices accordingly
                    update_matrices_names(study_data, bc_id, existing_constraint.operator, constraint.operator)

                # Updates the config before as the tree is based on the config
                study_data.config.bindings[existing_bindings[bc_id]] = constraint

                if constraint.time_step != existing_constraint.time_step:
                    # The user changed the time step, we need to update the matrix accordingly
                    for [target, new_matrix] in generate_replacement_matrices(
                        bc_id, study_version, constraint.operator
                    ):
                        # prepare matrix as a dict to save it in the tree
                        matrix_url = target.split("/")
                        study_data.tree.save(data={"data": new_matrix}, url=matrix_url)

                if constraint.group != existing_constraint.group:
                    assert isinstance(existing_constraint.group, str)
                    # We keep track of the removed groups for the scenario builder
                    old_groups[existing_constraint.group].remove(constraint.id)

            else:
                # We're creating a new constraint
                study_data.config.bindings.append(constraint)

            ini_key = bc_id_to_key_in_ini.get(constraint.id, get_next_available_key(ini_content))
            ini_content[ini_key] = serialize_binding_constraint(study_version, constraint)

        study_data.tree.save(ini_content, ["input", "bindingconstraints", "bindingconstraints"])

        if study_version >= STUDY_VERSION_8_7:
            # Groups
            removed_groups = {group for group in old_groups if not old_groups[group]}
            _remove_groups_from_scenario_builder(study_data, removed_groups)

    def _get_all_bc_matrices(self, term: str | None = None) -> BindingConstraintSeriesMapping:
        study_data = self.get_file_study()
        matrix_nodes = {}

        folder_node = study_data.tree.get_node(["input", "bindingconstraints"])
        assert isinstance(folder_node, FolderNode)
        tree = folder_node.build()
        del tree["bindingconstraints"]  # We only care about matrices
        for node_id, node in tree.items():
            assert isinstance(node, MatrixNode)
            if constraint_id := _get_constraint_id_from_matrix_file_name(node_id, term):
                # We only keep the constraints with the right terms
                matrix_nodes[node] = ConstraintId(constraint_id)

        matrices_mapping = self.get_impl().get_matrices_ids(list(matrix_nodes))

        result: BindingConstraintSeriesMapping = {}
        for node, matrix_id in matrices_mapping.items():
            constraint_id = matrix_nodes[node]
            result[constraint_id] = matrix_id

        return result

    def save_bc_matrices(
        self, series: BindingConstraintSeriesMapping, url_getter: Callable[[ConstraintId], list[str]]
    ) -> None:
        study_data = self.get_file_study()
        matrices_mapping: dict[str, list[MatrixNode]] = {}
        for constraint_id, series_id in series.items():
            url = url_getter(ConstraintId(constraint_id))
            node = study_data.tree.get_node(url)
            assert isinstance(node, MatrixNode)
            matrix_id = extract_matrix_id(series_id)
            matrices_mapping.setdefault(matrix_id, []).append(node)
        self.get_impl().save_matrices(matrices_mapping)

    @override
    def save_constraint_values_matrix(self, series: BindingConstraintSeriesMapping) -> None:
        self.save_bc_matrices(series, _get_values_matrix_path)

    @override
    def save_constraint_less_term_matrix(self, series: BindingConstraintSeriesMapping) -> None:
        self.save_bc_matrices(series, _get_less_term_matrix_path)

    @override
    def save_constraint_greater_term_matrix(self, series: BindingConstraintSeriesMapping) -> None:
        self.save_bc_matrices(series, _get_greater_term_matrix_path)

    @override
    def save_constraint_equal_term_matrix(self, series: BindingConstraintSeriesMapping) -> None:
        self.save_bc_matrices(series, _get_equal_term_matrix_path)

    @override
    def delete_constraints(self, constraints: list[BindingConstraint]) -> None:
        """Delete binding constraints and their associated matrix files from the study.

        Deleting a constraint not present in the study is a no-op.
        """
        study_data = self.get_file_study()
        ini_content = _get_all_constraints_ini(study_data)
        study_version = study_data.config.version

        ids_to_delete = {c.id for c in constraints}
        deleted_binding_constraints = []
        kept_binding_constraints = []
        old_groups = set()
        for key in list(ini_content.keys()):
            constraint = parse_binding_constraint(study_data.config.version, ini_content[key])
            if constraint.group:
                old_groups.add(constraint.group)
            if constraint.id in ids_to_delete:
                deleted_binding_constraints.append(constraint)
                del ini_content[key]
            else:
                kept_binding_constraints.append(constraint)

        # BC dict should start at index 0
        new_binding_constraints = {str(i): value for i, value in enumerate(ini_content.values())}

        study_data.tree.save(new_binding_constraints, ["input", "bindingconstraints", "bindingconstraints"])

        existing_files = study_data.tree.get(["input", "bindingconstraints"], depth=1)
        for bc in deleted_binding_constraints:
            if study_version < STUDY_VERSION_8_7:
                study_data.tree.delete(["input", "bindingconstraints", bc.id])
            else:
                for term in ["lt", "gt", "eq"]:
                    matrix_id = f"{bc.id}_{term}"
                    if matrix_id in existing_files:
                        study_data.tree.delete(["input", "bindingconstraints", matrix_id])

        if study_version >= STUDY_VERSION_8_7:
            new_groups = {bc.group for bc in kept_binding_constraints}
            removed_groups = old_groups - new_groups
            _remove_groups_from_scenario_builder(study_data, removed_groups)

        # Deleting the constraint in the configuration must be done AFTER deleting the files and folders.
        study_data.config.bindings = [bc for bc in study_data.config.bindings if bc.id not in ids_to_delete]


def _save_matrix(study_data: FileStudy, constraint_id: ConstraintId, term: str, series_id: str) -> None:
    study_data.tree.save(series_id, ["input", "bindingconstraints", f"{constraint_id}{term}"])


def _get_all_constraints_ini(study_data: FileStudy) -> dict[str, Any]:
    return study_data.tree.get(["input", "bindingconstraints", "bindingconstraints"])


def _remove_groups_from_scenario_builder(study_data: FileStudy, removed_groups: set[str]) -> None:
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


def generate_replacement_matrices(
    bc_id: ConstraintId,
    study_version: StudyVersion,
    current_operator: BindingConstraintOperator,
) -> Iterator[tuple[str, list[list[float]]]]:
    """
    Yield one (or two when operator is "BOTH") empty matrices.
    """
    if study_version < STUDY_VERSION_8_7:
        # Yield an empty matrix. The simulator accepts it and uses the correctly-sized
        # zero matrix for the constraint's time step internally.
        target = f"input/bindingconstraints/{bc_id}"
        yield target, []
    else:
        matrices_to_replace = OPERATOR_MATRIX_FILE_MAP[current_operator]
        for matrix_name in matrices_to_replace:
            matrix_id = matrix_name.format(bc_id=bc_id)
            target = f"input/bindingconstraints/{matrix_id}"
            yield target, []


def update_matrices_names(
    file_study: FileStudy,
    bc_id: ConstraintId,
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
