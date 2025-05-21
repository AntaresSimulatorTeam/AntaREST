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

from antarest.study.model import STUDY_VERSION_8_3
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.input.areas.item.adequacy_patch import (
    InputAreasAdequacyPatch,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.areas.item.optimization import InputAreasOptimization
from antarest.study.storage.rawstudy.model.filesystem.root.input.areas.item.ui import InputAreasUi


class InputAreasItem(FolderNode):
    @override
    def build(self) -> TREE:
        children: TREE = {
            "ui": InputAreasUi(self.config.next_file("ui.ini")),
            "optimization": InputAreasOptimization(
                self.config.next_file("optimization.ini"),
            ),
        }
        if self.config.version >= STUDY_VERSION_8_3:
            children["adequacy_patch"] = InputAreasAdequacyPatch(self.config.next_file("adequacy_patch.ini"))
        return children
