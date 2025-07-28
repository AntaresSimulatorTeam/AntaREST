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
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.variantstudy.business.matrix_constants.st_storage import series


class InputSTStorageConstraintsSTStorage(FolderNode):
    @override
    def build(self) -> TREE:
        children: TREE = {"additional_constraints": IniFileNode(self.config.next_file("additional-constraints.ini"))}
        matrices_ids = [d.stem for d in self.config.path.iterdir() if d.is_dir()]
        for matrix_id in matrices_ids:
            children[matrix_id] = InputSeriesMatrix(
                self.matrix_mapper,
                self.config.next_file(f"{matrix_id}.txt"),
                default_empty=series.additional_constraints,
            )

        return children
