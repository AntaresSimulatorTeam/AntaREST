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
from antarest.study.storage.rawstudy.model.filesystem.root.input.st_storage.clusters.area.area import InputSTStorageArea


class InputSTStorageClusters(FolderNode):
    # Each area has it own folder named after the area id.
    @override
    def build(self) -> TREE:
        children: TREE = {
            a: InputSTStorageArea(self.context, self.config.next_file(a), area=a) for a in self.config.area_names()
        }
        return children
