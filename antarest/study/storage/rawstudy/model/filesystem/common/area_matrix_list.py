from typing import Callable, Any

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


class AreaMatrixList(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            area: InputSeriesMatrix(
                self.context, config.next_file(f"{area}.txt")
            )
            for area in config.area_names()
        }
        return children


class HydroMatrixList(FolderNode):
    def __init__(
        self, context: ContextServer, config: FileStudyTreeConfig, area: str
    ):
        super().__init__(context, config)
        self.area = area

    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            "ror": InputSeriesMatrix(
                self.context, config.next_file("ror.txt")
            ),
            "storage": InputSeriesMatrix(
                self.context, config.next_file("storage.txt")
            ),
        }
        return children


class ThermalMatrixList(FolderNode):
    def __init__(
        self, context: ContextServer, config: FileStudyTreeConfig, area: str
    ):
        super().__init__(context, config)
        self.area = area

    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            thermal_cluster: InputSeriesMatrix(
                self.context, config.next_file(f"{thermal_cluster}.txt")
            )
            for thermal_cluster in config.get_thermal_names(self.area)
        }
        return children


class AreaMultipleMatrixList(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        klass: Callable[
            [ContextServer, FileStudyTreeConfig, str], INode[Any, Any, Any]
        ],
    ):
        super().__init__(context, config)
        self.klass = klass

    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            area: self.klass(self.context, config.next_file(area), area)
            for area in config.area_names()
        }
        return children
