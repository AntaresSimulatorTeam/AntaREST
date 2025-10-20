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

from typing import Any, Dict

from typing_extensions import override

from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE, INode
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency
from antarest.study.storage.rawstudy.model.filesystem.matrix.ts_generator_matrix import TsGeneratorMatrix


class TsGeneratorThermalAreaCluster(FolderNode):
    @override
    def build(self) -> TREE:
        ts_generator_matrices: Dict[str, INode[Any, Any, Any]] = {
            "forced outages": TsGeneratorMatrix(
                self.matrix_mapper,
                self.config.next_file("forced_outages.tsv"),
                freq=MatrixFrequency.DAILY,
            ),
            "planned outages": TsGeneratorMatrix(
                self.matrix_mapper,
                self.config.next_file("planned_outages.tsv"),
                freq=MatrixFrequency.DAILY,
            ),
        }

        return ts_generator_matrices
