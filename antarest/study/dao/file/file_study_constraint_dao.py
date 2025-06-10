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
from typing import Iterator, Sequence

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
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
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
        raise NotImplementedError()

    @override
    def get_constraint(self, constraint_id: str) -> BindingConstraint:
        raise NotImplementedError()

    @override
    def get_constraint_values_matrix(self, constraint_id: str) -> pd.DataFrame:
        raise NotImplementedError()

    @override
    def get_constraint_less_term_matrix(self, constraint_id: str) -> pd.DataFrame:
        raise NotImplementedError()

    @override
    def get_constraint_greater_term_matrix(self, constraint_id: str) -> pd.DataFrame:
        raise NotImplementedError()

    @override
    def get_constraint_equal_term_matrix(self, constraint_id: str) -> pd.DataFrame:
        raise NotImplementedError()

    @override
    def save_constraint(self, constraint: BindingConstraint) -> None:
        raise NotImplementedError()

    @override
    def save_constraints(self, constraints: Sequence[BindingConstraint]) -> None:
        raise NotImplementedError()

    @override
    def save_constraint_values_matrix(self, constraint_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @override
    def save_constraint_less_term_matrix(self, constraint_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @override
    def save_constraint_greater_term_matrix(self, constraint_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @override
    def save_constraint_equal_term_matrix(self, constraint_id: str, series_id: str) -> None:
        raise NotImplementedError()

    @override
    def delete_constraints(self, constraints: list[BindingConstraint]) -> None:
        raise NotImplementedError()


def _generate_replacement_matrices(
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
