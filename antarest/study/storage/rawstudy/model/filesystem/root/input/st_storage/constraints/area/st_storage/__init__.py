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

from antarest.matrixstore.matrix_uri_mapper import MatrixStorageContext
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import IniFileNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.rawstudy.model.filesystem.matrix.simulator_default import default_scenario_hourly


class InputSTStorageConstraintsSTStorage(FolderNode):
    def __init__(
        self, matrix_storage_context: MatrixStorageContext, config: FileStudyTreeConfig, area: str, storage: str
    ):
        super().__init__(matrix_storage_context, config)
        self.area = area
        self.storage = storage

    @override
    def build(self) -> TREE:
        children: TREE = {"additional_constraints": IniFileNode(self.config.next_file("additional-constraints.ini"))}
        for constraint in self.config.areas[self.area].st_storages_additional_constraints.get(self.storage, []):
            children[f"rhs_{constraint.id}"] = InputSeriesMatrix(
                self.matrix_storage_context,
                self.config.next_file(f"rhs_{constraint.id}.txt"),
                default_empty=default_scenario_hourly,
                should_exist=False,
            )

        return children
