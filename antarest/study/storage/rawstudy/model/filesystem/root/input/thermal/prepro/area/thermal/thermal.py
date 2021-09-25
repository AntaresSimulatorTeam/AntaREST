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


class InputThermalPreproAreaThermal(FolderNode):
    def build(self) -> TREE:
        children: TREE = {
            "data": InputSeriesMatrix(
                self.context, self.config.next_file("data.txt")
            ),
            "modulation": InputSeriesMatrix(
                self.context, self.config.next_file("modulation.txt")
            ),
        }
        return children
