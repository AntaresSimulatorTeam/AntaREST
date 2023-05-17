from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.constants import (
    default_4_fixed_hourly,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import (
    InputSeriesMatrix,
)


class InputReserves(FolderNode):
    def build(self) -> TREE:
        children: TREE = {
            a: InputSeriesMatrix(
                self.context,
                self.config.next_file(f"{a}.txt"),
                default_empty=default_4_fixed_hourly,
            )
            for a in self.config.area_names()
        }
        return children
