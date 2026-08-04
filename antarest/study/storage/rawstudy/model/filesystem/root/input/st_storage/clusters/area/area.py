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

from antarest.study.model import STUDY_VERSION_10_0
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.input.st_storage.clusters.area.list import (
    InputSTStorageAreaList,
)


class InputSTStorageArea(FolderNode):
    @override
    def build(self) -> TREE:
        # Each area has a folder containing a file named "list.ini"
        # If the area does not have any short-term storage cluster, the file is empty.
        children: TREE = {"list": InputSTStorageAreaList(self.config.next_file("list.ini"))}
        if self.config.version >= STUDY_VERSION_10_0:
            from antarest.study.storage.rawstudy.model.filesystem.yaml_file_node import YAMLFileNode

            children["reserve-participations"] = YAMLFileNode(self.config.next_file("reserve-participations.yml"))

        return children
