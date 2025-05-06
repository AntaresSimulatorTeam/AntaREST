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
from antarest.study.storage.rawstudy.model.filesystem.root.input.st_storage.series.area.area import (
    InputSTStorageSeriesArea,
)


class InputSTStorageSeries(FolderNode):
    # For each short-term storage, a time-series matrix is created after the name of the cluster.
    # This matrix is created inside the folder's area corresponding to the cluster.
    @override
    def build(self) -> TREE:
        children: TREE = {
            a: InputSTStorageSeriesArea(self.matrix_mapper, self.config.next_file(a), area=a)
            for a in self.config.area_names()
        }
        return children
