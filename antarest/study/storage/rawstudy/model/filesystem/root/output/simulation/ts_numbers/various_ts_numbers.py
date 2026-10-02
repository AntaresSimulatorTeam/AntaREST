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
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.ts_numbers.ts_numbers_data import (
    TsNumbersVector,
)


class ShortTermStorageTsNumbers(FolderNode):
    @override
    def build(self) -> TREE:
        children: TREE = {}
        for folder in self.config.path.iterdir():
            if folder.is_dir():
                children[folder.name] = GenericSubFolder(
                    self.matrix_storage_context, self.config.next_file(folder.name)
                )
        return children


class GenericSubFolder(FolderNode):
    @override
    def build(self) -> TREE:
        children: TREE = {}
        for folder in self.config.path.iterdir():
            if folder.is_dir():
                children[folder.name] = SubFolder(self.matrix_storage_context, self.config.next_file(folder.name))
        return children


class SubFolder(FolderNode):
    @override
    def build(self) -> TREE:
        children: TREE = {}
        for file in self.config.path.iterdir():
            children[file.stem] = TsNumbersVector(self.matrix_storage_context, self.config.next_file(file.name))
        return children
