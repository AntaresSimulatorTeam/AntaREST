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
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig, Simulation
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.common.utils import (
    OutputSimulationModeCommon,
)


class OutputSimulationModeMcInd(FolderNode):
    def __init__(
        self,
        context: MatrixUriMapper,
        config: FileStudyTreeConfig,
        simulation: Simulation,
    ):
        super().__init__(context, config)
        self.simulation = simulation

    @override
    def build(self) -> TREE:
        children: TREE = {
            f"{scn:05d}": OutputSimulationModeCommon(self.context, self.config.next_file(f"{scn:05d}"))
            for scn in self.simulation.playlist or range(1, self.simulation.nbyears + 1)
        }
        return children
