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
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcall.digest import DigestSynthesis
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcall.synthesis import OutputSynthesis


class OutputSimulationModeMcAllGrid(FolderNode):
    @override
    def build(self) -> TREE:
        files = [d.stem for d in self.config.path.iterdir()]
        children: TREE = {}
        for file in files:
            synthesis_class = DigestSynthesis if file == "digest" else OutputSynthesis
            children[file] = synthesis_class(self.matrix_mapper, self.config.next_file(f"{file}.txt"))
        return children
