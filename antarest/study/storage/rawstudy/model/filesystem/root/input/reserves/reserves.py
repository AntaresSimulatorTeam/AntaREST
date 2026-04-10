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
from typing_extensions import override

from antarest.study.model import STUDY_VERSION_10_0
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.rawstudy.model.filesystem.matrix.simulator_default import default_4_fixed_hourly
from antarest.study.storage.rawstudy.model.filesystem.root.input.reserves.area_reserves import (
    InputReservesAreaFolder,
)


class InputReserves(FolderNode):
    @override
    def build(self) -> TREE:
        if self.config.version >= STUDY_VERSION_10_0:
            return {
                a: InputReservesAreaFolder(
                    self.matrix_mapper,
                    self.config.next_file(a),
                    matrix_node=InputSeriesMatrix(
                        self.matrix_mapper,
                        self.config.next_file(f"{a}.txt"),
                        default_empty=default_4_fixed_hourly,
                    ),
                )
                for a in self.config.area_names()
            }
        return {
            a: InputSeriesMatrix(
                self.matrix_mapper,
                self.config.next_file(f"{a}.txt"),
                default_empty=default_4_fixed_hourly,
            )
            for a in self.config.area_names()
        }
