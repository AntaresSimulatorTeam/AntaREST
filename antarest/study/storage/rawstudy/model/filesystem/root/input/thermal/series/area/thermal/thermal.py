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
from antarest.study.storage.rawstudy.model.filesystem.matrix.constants import default_scenario_hourly
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency


class InputThermalSeriesAreaThermal(FolderNode):
    @override
    def build(self) -> TREE:
        children: TREE = {
            "series": InputSeriesMatrix(
                self.matrix_mapper,
                self.config.next_file("series.txt"),
                default_empty=default_scenario_hourly,
            ),
        }
        if self.config.version >= 870:
            children["CO2Cost"] = InputSeriesMatrix(
                self.matrix_mapper,
                self.config.next_file("CO2Cost.txt"),
                freq=MatrixFrequency.HOURLY,
                default_empty=default_scenario_hourly,
            )
            children["fuelCost"] = InputSeriesMatrix(
                self.matrix_mapper,
                self.config.next_file("fuelCost.txt"),
                freq=MatrixFrequency.HOURLY,
                default_empty=default_scenario_hourly,
            )
        return children
