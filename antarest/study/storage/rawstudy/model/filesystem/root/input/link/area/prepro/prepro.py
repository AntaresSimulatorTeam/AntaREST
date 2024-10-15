# Copyright (c) 2024, RTE (https://www.rte-france.com)
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

from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix


class InputLinkAreaPrepro(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        area: str,
    ):
        super().__init__(context, config)
        self.area = area

    def build(self) -> TREE:
        children: TREE = {}
        for area_to in self.config.get_links(self.area):
            children[f"{area_to}_direct"] = InputSeriesMatrix(
                self.context,
                self.config.next_file(f"{area_to}_direct.txt"),
            )
            children[f"{area_to}_indirect"] = InputSeriesMatrix(
                self.context,
                self.config.next_file(f"{area_to}_indirect.txt"),
            )
            children[f"{area_to}_mod"] = InputSeriesMatrix(
                self.context,
                self.config.next_file(f"{area_to}_mod.txt"),
            )
        return children
