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
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix_storage_context import MatrixStorageContext
from antarest.study.storage.rawstudy.model.filesystem.root.input.thermal.cluster.area.list import (
    InputThermalClustersAreaList,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.thermal.cluster.area.reserves_ini import (
    InputThermalClustersAreaReservesIni,
)


class InputThermalClustersArea(FolderNode):
    def __init__(
        self,
        matrix_storage_context: MatrixStorageContext,
        config: FileStudyTreeConfig,
        area: str,
    ):
        super().__init__(matrix_storage_context, config)
        self.area = area

    @override
    def build(self) -> TREE:
        children: TREE = {"list": InputThermalClustersAreaList(self.config.next_file("list.ini"))}
        if self.config.version >= STUDY_VERSION_10_0:
            children["reserves"] = InputThermalClustersAreaReservesIni(self.config.next_file("reserves.ini"))
        return children
