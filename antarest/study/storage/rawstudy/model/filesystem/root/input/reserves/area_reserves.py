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

from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.rawstudy.model.filesystem.matrix.simulator_default import default_scenario_hourly
from antarest.study.storage.rawstudy.model.filesystem.root.input.reserves.reserves_ini import InputReservesIni


class InputReservesAreaFolder(FolderNode):
    @override
    def build(self) -> TREE:
        area_id = self.config.path.name
        tree: TREE = {
            "reserves": InputReservesIni(self.config.next_file("reserves.ini")),
        }
        for reserve_id in self.config.areas[area_id].reserves:
            tree[reserve_id] = InputSeriesMatrix(
                self.matrix_storage_context,
                self.config.next_file(f"{reserve_id}.txt"),
                default_empty=default_scenario_hourly,
                should_exist=False,
            )
        return tree
