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
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency
from antarest.study.storage.rawstudy.model.filesystem.matrix.output_series_matrix import (
    BindingConstraintOutputSeriesMatrix,
)


class OutputSimulationBindingConstraintItem(FolderNode):
    @override
    def build(self) -> TREE:
        existing_files = [d.stem.replace("binding-constraints-", "") for d in self.config.path.iterdir()]
        children: TREE = {
            f"binding-constraints-{freq}": BindingConstraintOutputSeriesMatrix(
                self.matrix_mapper,
                self.config.next_file(f"binding-constraints-{freq}.txt"),
                MatrixFrequency(freq),
            )
            for freq in existing_files
        }
        return children
