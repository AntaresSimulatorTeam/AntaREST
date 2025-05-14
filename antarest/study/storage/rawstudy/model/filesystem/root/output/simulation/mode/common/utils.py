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
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.common.areas import (
    OutputSimulationAreas,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.common.binding_const import (
    OutputSimulationBindingConstraintItem,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.common.links import (
    OutputSimulationLinks,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcall.grid import (
    OutputSimulationModeMcAllGrid,
)

OUTPUT_MAPPING = {
    "areas": OutputSimulationAreas,
    "grid": OutputSimulationModeMcAllGrid,
    "links": OutputSimulationLinks,
    "binding_constraints": OutputSimulationBindingConstraintItem,
}


class OutputSimulationModeCommon(FolderNode):
    @override
    def build(self) -> TREE:
        if not self.config.output_path:
            return {}
        children: TREE = {}
        for key, simulation_class in OUTPUT_MAPPING.items():
            if (self.config.path / key).exists():
                children[key] = simulation_class(self.matrix_mapper, self.config.next_file(key))
        return children
