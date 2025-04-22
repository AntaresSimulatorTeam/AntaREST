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
from antarest.study.storage.rawstudy.model.filesystem.root.input.thermal.areas_ini import InputThermalAreasIni
from antarest.study.storage.rawstudy.model.filesystem.root.input.thermal.cluster.cluster import InputThermalClusters
from antarest.study.storage.rawstudy.model.filesystem.root.input.thermal.prepro.prepro import InputThermalPrepro
from antarest.study.storage.rawstudy.model.filesystem.root.input.thermal.series.series import InputThermalSeries


class InputThermal(FolderNode):
    @override
    def build(self) -> TREE:
        children: TREE = {
            "clusters": InputThermalClusters(self.matrix_mapper, self.config.next_file("clusters")),
            "prepro": InputThermalPrepro(self.matrix_mapper, self.config.next_file("prepro")),
            "series": InputThermalSeries(self.matrix_mapper, self.config.next_file("series")),
            "areas": InputThermalAreasIni(self.config.next_file("areas.ini")),
        }
        return children
