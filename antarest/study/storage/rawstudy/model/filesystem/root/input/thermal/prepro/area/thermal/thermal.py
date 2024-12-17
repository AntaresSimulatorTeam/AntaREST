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
from typing_extensions import override

from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency


class InputThermalPreproAreaThermal(FolderNode):
    """
    Folder containing thermal cluster data: `input/thermal/prepro/{area_id}/{cluster_id}`.

    This folder contains the following files:

    - `data.txt` (matrix): TS Generator matrix (daily)
    - `modulation.txt` (matrix): Modulation matrix (hourly)
    """

    @override
    def build(self) -> TREE:
        children: TREE = {
            "data": InputSeriesMatrix(self.context, self.config.next_file("data.txt"), freq=MatrixFrequency.DAILY),
            "modulation": InputSeriesMatrix(self.context, self.config.next_file("modulation.txt")),
        }
        return children
