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
from antarest.study.storage.rawstudy.model.filesystem.root.input.st_storage.constraints.area.st_storage import (
    InputSTStorageConstraintsSTStorage,
)


class InputSTStorageConstraintsArea(FolderNode):
    def __init__(self, matrix_mapper: MatrixUriMapper, config: FileStudyTreeConfig, area: str):
        super().__init__(matrix_mapper, config)
        self.area = area

    @override
    def build(self) -> TREE:
        children: TREE = {
            sts: InputSTStorageConstraintsSTStorage(self.matrix_mapper, self.config.next_file(sts), self.area, sts)
            for sts in self.config.get_st_storage_ids(self.area)
        }
        return children
