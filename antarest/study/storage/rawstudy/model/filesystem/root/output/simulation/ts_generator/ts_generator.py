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

from collections.abc import Callable
from typing import Any

from typing_extensions import override

from antarest.study.storage.rawstudy.model.filesystem.common.area_matrix_list import (
    AreaMatrixList,
    AreaMultipleMatrixList,
    HydroMatrixList,
    ThermalMatrixList,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE, INode
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix_storage_context import MatrixStorageContext


class OutputSimulationTsGeneratorSimpleMatrixList(FolderNode):
    @override
    def build(self) -> TREE:
        children: TREE = {
            "mc-0": AreaMatrixList(self.matrix_storage_context, self.config.next_file("mc-0")),
        }
        return children


class OutputSimulationTsGeneratorCustomMatrixList(FolderNode):
    def __init__(
        self,
        matrix_storage_context: MatrixStorageContext,
        config: FileStudyTreeConfig,
        klass: Callable[
            [
                MatrixStorageContext,
                FileStudyTreeConfig,
                str,
                Callable[
                    [MatrixStorageContext, FileStudyTreeConfig],
                    INode[Any, Any, Any],
                ],
            ],
            INode[Any, Any, Any],
        ],
    ):
        super().__init__(matrix_storage_context, config)
        self.klass = klass

    @override
    def build(self) -> TREE:
        children: TREE = {
            "mc-0": AreaMultipleMatrixList(
                self.matrix_storage_context,
                self.config.next_file("mc-0"),
                self.klass,
                InputSeriesMatrix,
            ),
        }
        return children


class OutputSimulationTsGenerator(FolderNode):
    @override
    def build(self) -> TREE:
        children: TREE = {}
        for output_type in ["load", "solar", "wind"]:
            if (self.config.path / output_type).exists():
                children[output_type] = OutputSimulationTsGeneratorSimpleMatrixList(
                    self.matrix_storage_context, self.config.next_file(output_type)
                )
        if (self.config.path / "hydro").exists():
            children["hydro"] = OutputSimulationTsGeneratorCustomMatrixList(
                self.matrix_storage_context, self.config.next_file("hydro"), HydroMatrixList
            )
        if (self.config.path / "thermal").exists():
            children["thermal"] = OutputSimulationTsGeneratorCustomMatrixList(
                self.matrix_storage_context, self.config.next_file("thermal"), ThermalMatrixList
            )
        return children
