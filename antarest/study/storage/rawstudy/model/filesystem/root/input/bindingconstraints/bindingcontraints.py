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
from typing_extensions import override

from antarest.study.business.model.binding_constraint_model import OPERATOR_MATRICES_MAP, BindingConstraintFrequency
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency
from antarest.study.storage.rawstudy.model.filesystem.root.input.bindingconstraints.bindingconstraints_ini import (
    BindingConstraintsIni,
)
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


class BindingConstraints(FolderNode):
    """
    Handle the binding constraints folder which contains the binding constraints
    configuration and matrices.
    """

    @override
    def build(self) -> TREE:
        cfg = self.config
        frequency_mapping = {
            BindingConstraintFrequency.HOURLY: MatrixFrequency.HOURLY,
            BindingConstraintFrequency.DAILY: MatrixFrequency.DAILY,
            BindingConstraintFrequency.WEEKLY: MatrixFrequency.DAILY,
        }
        if cfg.version < 870:
            default_matrices = {
                BindingConstraintFrequency.HOURLY: default_bc_hourly_86,
                BindingConstraintFrequency.DAILY: default_bc_weekly_daily_86,
                BindingConstraintFrequency.WEEKLY: default_bc_weekly_daily_86,
            }
            children: TREE = {
                binding.id: InputSeriesMatrix(
                    self.matrix_mapper,
                    self.config.next_file(f"{binding.id}.txt"),
                    freq=frequency_mapping[binding.time_step],
                    nb_columns=3,
                    default_empty=default_matrices[binding.time_step],
                )
                for binding in self.config.bindings
            }
        else:
            default_matrices = {
                BindingConstraintFrequency.HOURLY: default_bc_hourly_87,
                BindingConstraintFrequency.DAILY: default_bc_weekly_daily_87,
                BindingConstraintFrequency.WEEKLY: default_bc_weekly_daily_87,
            }
            children = {}
            for binding in self.config.bindings:
                terms = OPERATOR_MATRICES_MAP[binding.operator]
                for term in terms:
                    matrix_id = f"{binding.id}_{term}"
                    children[matrix_id] = InputSeriesMatrix(
                        self.matrix_mapper,
                        self.config.next_file(f"{matrix_id}.txt"),
                        freq=frequency_mapping[binding.time_step],
                        nb_columns=1 if term in ["lt", "gt"] else None,
                        default_empty=default_matrices[binding.time_step],
                    )
        children["bindingconstraints"] = BindingConstraintsIni(self.config.next_file("bindingconstraints.ini"))

        return children
