from typing import Any, Callable

from antarest.study.storage.rawstudy.model.filesystem.common.area_matrix_list import (
    AreaMatrixList,
    AreaMultipleMatrixList,
    HydroMatrixList,
    ThermalMatrixList,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE, INode
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import (
    InputSeriesMatrix,
)


class OutputSimulationTsGeneratorSimpleMatrixList(FolderNode):
    def build(self) -> TREE:
        children: TREE = {
            "mc-0": AreaMatrixList(
                self.context, self.config.next_file("mc-0")
            ),
        }
        return children


class OutputSimulationTsGeneratorCustomMatrixList(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        klass: Callable[
            [
                ContextServer,
                FileStudyTreeConfig,
                str,
                Callable[
                    [ContextServer, FileStudyTreeConfig],
                    INode[Any, Any, Any],
                ],
            ],
            INode[Any, Any, Any],
        ],
    ):
        super().__init__(context, config)
        self.klass = klass

    def build(self) -> TREE:
        children: TREE = {
            "mc-0": AreaMultipleMatrixList(
                self.context,
                self.config.next_file("mc-0"),
                self.klass,
                InputSeriesMatrix,
            ),
        }
        return children


class OutputSimulationTsGenerator(FolderNode):
    def build(self) -> TREE:
        children: TREE = {
            "hydro": OutputSimulationTsGeneratorCustomMatrixList(
                self.context, self.config.next_file("hydro"), HydroMatrixList
            ),
            "load": OutputSimulationTsGeneratorSimpleMatrixList(
                self.context, self.config.next_file("load")
            ),
            "solar": OutputSimulationTsGeneratorSimpleMatrixList(
                self.context, self.config.next_file("solar")
            ),
            "wind": OutputSimulationTsGeneratorSimpleMatrixList(
                self.context, self.config.next_file("wind")
            ),
            "thermal": OutputSimulationTsGeneratorCustomMatrixList(
                self.context,
                self.config.next_file("thermal"),
                ThermalMatrixList,
            ),
        }
        return children
