from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import (
    InputSeriesMatrix,
)


class ClusteredRenewableSeries(FolderNode):
    def build(self) -> TREE:
        series_config = self.config.next_file("series.txt")
        children: TREE = {
            "series": InputSeriesMatrix(self.context, series_config)
        }
        return children


class ClusteredRenewableClusterSeries(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        area: str,
    ):
        super().__init__(context, config)
        self.area = area

    def build(self) -> TREE:
        children: TREE = {
            renewable: ClusteredRenewableSeries(
                self.context, self.config.next_file(renewable)
            )
            for renewable in self.config.get_renewable_names(self.area)
        }
        return children


class ClusteredRenewableAreaSeries(FolderNode):
    def build(self) -> TREE:
        return {
            area: ClusteredRenewableClusterSeries(
                self.context, self.config.next_file(area), area
            )
            for area in self.config.area_names()
        }
