from typing import Callable, Any, Optional, Dict

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
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        prefix: str = "",
        matrix_class: Callable[..., INode[Any, Any, Any]] = InputSeriesMatrix,
        additional_matrix_params: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(context, config)
        self.prefix = prefix
        self.matrix_class = matrix_class
        self.additional_matrix_params = additional_matrix_params

    def build(self) -> TREE:
        children: TREE = {
            f"{self.prefix}{area}": self.matrix_class(
                self.context,
                self.config.next_file(f"{self.prefix}{area}.txt"),
                **(self.additional_matrix_params or {}),
            )
            for area in self.config.area_names()
        }
        return children


class HydroMatrixList(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        area: str,
        matrix_class: Callable[
            [ContextServer, FileStudyTreeConfig], INode[Any, Any, Any]
        ],
    ):
        super().__init__(context, config)
        self.area = area
        self.matrix_class = matrix_class

    def build(self) -> TREE:
        children: TREE = {
            "ror": self.matrix_class(
                self.context, self.config.next_file("ror.txt")
            ),
            "storage": self.matrix_class(
                self.context, self.config.next_file("storage.txt")
            ),
        }
        return children


class ThermalMatrixList(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        area: str,
        matrix_class: Callable[
            [ContextServer, FileStudyTreeConfig], INode[Any, Any, Any]
        ],
    ):
        super().__init__(context, config)
        self.area = area
        self.matrix_class = matrix_class

    def build(self) -> TREE:
        children: TREE = {
            thermal_cluster: self.matrix_class(
                self.context, self.config.next_file(f"{thermal_cluster}.txt")
            )
            for thermal_cluster in self.config.get_thermal_names(self.area)
        }
        return children


class AreaMultipleMatrixList(FolderNode):
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
        matrix_class: Callable[
            [ContextServer, FileStudyTreeConfig], INode[Any, Any, Any]
        ],
    ):
        super().__init__(context, config)
        self.klass = klass
        self.matrix_class = matrix_class

    def build(self) -> TREE:
        children: TREE = {
            area: self.klass(
                self.context,
                self.config.next_file(area),
                area,
                self.matrix_class,
            )
            for area in self.config.area_names()
        }
        return children
