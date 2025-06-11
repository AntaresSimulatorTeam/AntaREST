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
from abc import ABC, abstractmethod
from typing import Any, Iterator, Sequence

import pandas as pd
from antares.study.version import StudyVersion
from typing_extensions import override

from antarest.study.business.model.binding_constraint_model import (
    OPERATOR_MATRIX_FILE_MAP,
    BindingConstraint,
    BindingConstraintFrequency,
    BindingConstraintOperator,
)
from antarest.study.dao.api.binding_constraint_dao import ConstraintDao
from antarest.study.model import STUDY_VERSION_8_7
from antarest.study.storage.rawstudy.model.filesystem.config.binding_constraint import (
    parse_binding_constraint,
    serialize_binding_constraint,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.variantstudy.business.matrix_constants.binding_constraint.series_after_v87 import (
    default_bc_hourly as default_bc_hourly_87,
)
from antarest.study.storage.variantstudy.business.matrix_constants.binding_constraint.series_after_v87 import (
    default_bc_weekly_daily as default_bc_weekly_daily_87,
)
from antarest.study.storage.variantstudy.business.matrix_constants.binding_constraint.series_before_v87 import (
    default_bc_hourly as default_bc_hourly_86,
)
from antarest.study.storage.variantstudy.business.matrix_constants.binding_constraint.series_before_v87 import (
    default_bc_weekly_daily as default_bc_weekly_daily_86,
)


class FileStudyConstraintDao(ConstraintDao, ABC):
    @abstractmethod
    def get_file_study(self) -> FileStudy:
        pass

    @override
    def get_all_constraints(self) -> dict[str, BindingConstraint]:
        file_study = self.get_file_study()
        version = file_study.config.version
        config = _get_all_constraints_ini(file_study)

        constraints_by_id: dict[str, BindingConstraint] = {}

        for constraint_ini in config.values():
            constraint = parse_binding_constraint(version, constraint_ini)
            constraints_by_id[constraint.id] = constraint
        return constraints_by_id

    @override
    def get_constraint(self, constraint_id: str) -> BindingConstraint:
        return self.get_all_constraints()[constraint_id]

    @override
    def get_constraint_values_matrix(self, constraint_id: str) -> pd.DataFrame:
        return _get_matrix(self.get_file_study(), constraint_id, "")

    @override
    def get_constraint_less_term_matrix(self, constraint_id: str) -> pd.DataFrame:
        return _get_matrix(self.get_file_study(), constraint_id, "_lt")

    @override
    def get_constraint_greater_term_matrix(self, constraint_id: str) -> pd.DataFrame:
        return _get_matrix(self.get_file_study(), constraint_id, "_gt")

    @override
    def get_constraint_equal_term_matrix(self, constraint_id: str) -> pd.DataFrame:
        return _get_matrix(self.get_file_study(), constraint_id, "_eq")

    @override
    def save_constraints(self, constraints: Sequence[BindingConstraint]) -> None:
        study_data = self.get_file_study()
        study_version = study_data.config.version
        ini_content = _get_all_constraints_ini(study_data)

        id_by_key = {}
        old_groups = set()
        for key, bc in ini_content.items():
            constraint = parse_binding_constraint(study_data.config.version, bc)
            id_by_key[constraint.id] = key
            if constraint.group:
                old_groups.add(constraint.group)

        existing_bindings = {bc.id: k for k, bc in enumerate(study_data.config.bindings)}

        for constraint in constraints:
            if constraint.id in existing_bindings:
                study_data.config.bindings[existing_bindings[constraint.id]] = constraint
            else:
                study_data.config.bindings.append(constraint)

            ini_key = id_by_key.get(constraint.id, str(len(ini_content)))
            ini_content[ini_key] = serialize_binding_constraint(study_version, constraint)

        study_data.tree.save(ini_content, ["input", "bindingconstraints", "bindingconstraints"])

        if study_version >= STUDY_VERSION_8_7:
            # Groups
            new_groups = {bc.group for bc in constraints}
            removed_groups = old_groups - new_groups
            _remove_groups_from_scenario_builder(study_data, removed_groups)

    @override
    def save_constraint_values_matrix(self, constraint_id: str, series_id: str) -> None:
        _save_matrix(self.get_file_study(), constraint_id, "", series_id)

    @override
    def save_constraint_less_term_matrix(self, constraint_id: str, series_id: str) -> None:
        _save_matrix(self.get_file_study(), constraint_id, "_lt", series_id)

    @override
    def save_constraint_greater_term_matrix(self, constraint_id: str, series_id: str) -> None:
        _save_matrix(self.get_file_study(), constraint_id, "_gt", series_id)

    @override
    def save_constraint_equal_term_matrix(self, constraint_id: str, series_id: str) -> None:
        _save_matrix(self.get_file_study(), constraint_id, "_eq", series_id)

    @override
    def delete_constraints(self, constraints: list[BindingConstraint]) -> None:
        study_data = self.get_file_study()
        ini_content = _get_all_constraints_ini(study_data)
        study_version = study_data.config.version

        deleted_binding_constraints = []
        kept_binding_constraints = []
        old_groups = set()
        for key, bc in ini_content.items():
            constraint = parse_binding_constraint(study_data.config.version, bc)
            if constraint.group:
                old_groups.add(constraint.group)
            if constraint in constraints:
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
        for constraint in constraints:
            study_data.config.bindings.remove(constraint)


def _get_matrix(study_data: FileStudy, constraint_id: str, term: str) -> pd.DataFrame:
    node = study_data.tree.get_node(["input", "bindingconstraints", f"{constraint_id}{term}"])
    assert isinstance(node, InputSeriesMatrix)
    return node.parse_as_dataframe()


def _save_matrix(study_data: FileStudy, constraint_id: str, term: str, series_id: str) -> None:
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
    bc_id: str,
    study_version: StudyVersion,
    new_time_step: BindingConstraintFrequency,
    current_operator: BindingConstraintOperator,
) -> Iterator[tuple[str, list[list[float]]]]:
    """
    Yield one (or two when operator is "BOTH") matrices initialized with default values.
    """
    if study_version < STUDY_VERSION_8_7:
        target = f"input/bindingconstraints/{bc_id}"
        matrix = {
            BindingConstraintFrequency.HOURLY: default_bc_hourly_86,
            BindingConstraintFrequency.DAILY: default_bc_weekly_daily_86,
            BindingConstraintFrequency.WEEKLY: default_bc_weekly_daily_86,
        }[new_time_step].tolist()
        yield target, matrix
    else:
        matrix = {
            BindingConstraintFrequency.HOURLY: default_bc_hourly_87,
            BindingConstraintFrequency.DAILY: default_bc_weekly_daily_87,
            BindingConstraintFrequency.WEEKLY: default_bc_weekly_daily_87,
        }[new_time_step].tolist()
        matrices_to_replace = OPERATOR_MATRIX_FILE_MAP[current_operator]
        for matrix_name in matrices_to_replace:
            matrix_id = matrix_name.format(bc_id=bc_id)
            target = f"input/bindingconstraints/{matrix_id}"
            yield target, matrix
