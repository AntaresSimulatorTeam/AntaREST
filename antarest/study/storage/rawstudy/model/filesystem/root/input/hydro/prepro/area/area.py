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
import numpy as np
from typing_extensions import override

from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.rawstudy.model.filesystem.root.input.hydro.prepro.area.prepro import (
    InputHydroPreproAreaPrepro,
)

default_energy = np.zeros((12, 5), dtype=np.float64)
default_energy.flags.writeable = False


class InputHydroPreproArea(FolderNode):
    @override
    def build(self) -> TREE:
        children: TREE = {
            "energy": InputSeriesMatrix(
                self.context, self.config.next_file("energy.txt"), default_empty=default_energy
            ),
            "prepro": InputHydroPreproAreaPrepro(self.context, self.config.next_file("prepro.ini")),
        }
        return children
