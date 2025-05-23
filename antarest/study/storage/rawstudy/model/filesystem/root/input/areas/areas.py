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

from antarest.matrixstore.matrix_uri_mapper import MatrixUriMapper
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.input.areas.item.item import InputAreasItem
from antarest.study.storage.rawstudy.model.filesystem.root.input.areas.list import InputAreasList
from antarest.study.storage.rawstudy.model.filesystem.root.input.areas.sets import InputAreasSets


class InputAreas(FolderNode):
    def __init__(self, matrix_mapper: MatrixUriMapper, config: FileStudyTreeConfig):
        super().__init__(matrix_mapper, config, ["list", "sets"])

    @override
    def build(self) -> TREE:
        children: TREE = {
            a: InputAreasItem(self.matrix_mapper, self.config.next_file(a)) for a in self.config.area_names()
        }
        children["list"] = InputAreasList(self.matrix_mapper, self.config.next_file("list.txt"))
        children["sets"] = InputAreasSets(self.config.next_file("sets.ini"))
        return children
