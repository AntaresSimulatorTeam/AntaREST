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

from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.variantstudy.business.matrix_constants.st_storage import series


class InputSTStorageAreaStorage(FolderNode):
    @override
    def build(self) -> TREE:
        children: TREE = {
            "pmax_injection": InputSeriesMatrix(
                self.matrix_mapper,
                self.config.next_file("PMAX-injection.txt"),
                default_empty=series.pmax_injection,
            ),
            "pmax_withdrawal": InputSeriesMatrix(
                self.matrix_mapper,
                self.config.next_file("PMAX-withdrawal.txt"),
                default_empty=series.pmax_withdrawal,
            ),
            "inflows": InputSeriesMatrix(
                self.matrix_mapper,
                self.config.next_file("inflows.txt"),
                default_empty=series.inflows,
            ),
            "lower_rule_curve": InputSeriesMatrix(
                self.matrix_mapper,
                self.config.next_file("lower-rule-curve.txt"),
                default_empty=series.lower_rule_curve,
            ),
            "upper_rule_curve": InputSeriesMatrix(
                self.matrix_mapper,
                self.config.next_file("upper-rule-curve.txt"),
                default_empty=series.upper_rule_curve,
            ),
        }
        return children
