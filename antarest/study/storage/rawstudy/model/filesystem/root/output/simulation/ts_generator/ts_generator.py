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

from typing import Any, Callable

from typing_extensions import override

from antarest.matrixstore.uri_resolver_service import MatrixUriMapper
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


class OutputSimulationTsGeneratorSimpleMatrixList(FolderNode):
    @override
    def build(self) -> TREE:
        children: TREE = {
            "mc-0": AreaMatrixList(self.matrix_mapper, self.config.next_file("mc-0")),
        }
        return children


class OutputSimulationTsGeneratorCustomMatrixList(FolderNode):
    def __init__(
        self,
        matrix_mapper: MatrixUriMapper,
        config: FileStudyTreeConfig,
        klass: Callable[
            [
                MatrixUriMapper,
                FileStudyTreeConfig,
                str,
                Callable[
                    [MatrixUriMapper, FileStudyTreeConfig],
                    INode[Any, Any, Any],
                ],
            ],
            INode[Any, Any, Any],
        ],
    ):
        super().__init__(matrix_mapper, config)
        self.klass = klass

    @override
    def build(self) -> TREE:
        children: TREE = {
            "mc-0": AreaMultipleMatrixList(
                self.matrix_mapper,
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
                    self.matrix_mapper, self.config.next_file(output_type)
                )
        if (self.config.path / "hydro").exists():
            children["hydro"] = OutputSimulationTsGeneratorCustomMatrixList(
                self.matrix_mapper, self.config.next_file("hydro"), HydroMatrixList
            )
        if (self.config.path / "thermal").exists():
            children["thermal"] = OutputSimulationTsGeneratorCustomMatrixList(
                self.matrix_mapper, self.config.next_file("thermal"), ThermalMatrixList
            )
        return children
