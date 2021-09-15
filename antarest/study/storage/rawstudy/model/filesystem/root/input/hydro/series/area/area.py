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


class InputHydroSeriesArea(FolderNode):
    def build(self) -> TREE:
        children: TREE = {
            # TODO mod is monthly on version < 650, then daily afterward
            "mod": InputSeriesMatrix(
                self.context, self.config.next_file("mod.txt")
            ),
            "ror": InputSeriesMatrix(
                self.context, self.config.next_file("ror.txt")
            ),
        }
        return children
