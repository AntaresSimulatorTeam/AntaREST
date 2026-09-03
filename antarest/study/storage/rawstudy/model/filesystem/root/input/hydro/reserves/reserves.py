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
from antarest.study.storage.rawstudy.model.filesystem.root.input.hydro.reserves.area import InputHydroReservesArea


class InputHydroReserves(FolderNode):
    # Each area has its own folder named after the area id.
    @override
    def build(self) -> TREE:
        return {
            area_id: InputHydroReservesArea(self.matrix_storage_context, self.config.next_file(area_id))
            for area_id in self.config.area_names()
        }
