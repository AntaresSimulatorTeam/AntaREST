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
from antarest.study.storage.rawstudy.model.filesystem.bucket_node import BucketNode
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix


class ExpansionMatrixResources(BucketNode):
    def __init__(self, matrix_mapper: MatrixUriMapper, config: FileStudyTreeConfig):
        super().__init__(matrix_mapper, config, None, default_file_node=InputSeriesMatrix)

    @override
    def build(self) -> TREE:
        children: TREE = {}
        for resource in self.config.path.iterdir():
            if resource.is_file():
                node = InputSeriesMatrix(self.matrix_mapper, self.config.next_file(resource.name))
                children[node.config.path.name] = node

        return children
