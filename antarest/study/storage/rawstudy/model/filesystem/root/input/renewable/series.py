from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import (
    InputSeriesMatrix,
)


class ClusteredRenewableSeries(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {}
        series_config = config.next_file("series.txt")
        if series_config.path.exists():
            children = {
                "series": InputSeriesMatrix(self.context, series_config)
            }
        return children


class ClusteredRenewableAreaSeries(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        return {
            area: ClusteredRenewableSeries(
                self.context, config.next_file(area)
            )
            for area in config.area_names()
        }
