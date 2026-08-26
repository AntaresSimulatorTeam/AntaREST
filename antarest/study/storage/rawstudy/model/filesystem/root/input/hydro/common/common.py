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

from antarest.study.model import STUDY_VERSION_10_2
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.input.hydro.common.capacity.capacity import (
    InputHydroCommonCapacity,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.hydro.common.reserves.reserves import (
    InputHydroCommonReserves,
)


class InputHydroCommon(FolderNode):
    @override
    def build(self) -> TREE:
        children: TREE = {
            "capacity": InputHydroCommonCapacity(self.matrix_storage_context, self.config.next_file("capacity"))
        }
        if self.config.version >= STUDY_VERSION_10_2:
            # Reserve participations of the long-term storage, one folder per area.
            children["reserves"] = InputHydroCommonReserves(
                self.matrix_storage_context, self.config.next_file("reserves")
            )
        return children
