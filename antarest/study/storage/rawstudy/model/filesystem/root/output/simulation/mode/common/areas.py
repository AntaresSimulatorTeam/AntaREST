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

from antarest.matrixstore.uri_resolver_service import MatrixUriMapper
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.common.area import (
    OutputSimulationAreaItem as Area,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.common.set import (
    OutputSimulationSet as Set,
)


class OutputSimulationAreas(FolderNode):
    def __init__(
        self,
        matrix_mapper: MatrixUriMapper,
        config: FileStudyTreeConfig,
    ) -> None:
        super().__init__(matrix_mapper, config)

    @override
    def build(self) -> TREE:
        areas = set()
        sets = set()
        for file in self.config.path.iterdir():
            name = file.stem
            if "@" in name:
                sets.add(name)
            else:
                areas.add(name)
        children: TREE = {a: Area(self.matrix_mapper, self.config.next_file(a), area=a) for a in areas}

        for s in sets:
            children[s] = Set(self.matrix_mapper, self.config.next_file(s), set=s)
        return children
