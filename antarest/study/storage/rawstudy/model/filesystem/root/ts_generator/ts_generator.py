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
from antarest.study.storage.rawstudy.model.filesystem.root.ts_generator.thermal.thermal import TsGeneratorThermal


class TsGenerator(FolderNode):
    """
    Handle the ts-generator folder which contains all the ts-generated planned and forced outage info.
    """

    @override
    def build(self) -> TREE:
        config = self.config
        children: TREE = {
            "thermal": TsGeneratorThermal(self.matrix_mapper, config.next_file("thermal")),
        }
        return children
