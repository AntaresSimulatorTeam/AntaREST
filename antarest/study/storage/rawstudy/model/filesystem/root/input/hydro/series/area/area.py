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
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            "mod": InputSeriesMatrix(
                self.context, config.next_file("mod.txt")
            ),
            "ror": InputSeriesMatrix(
                self.context, config.next_file("ror.txt")
            ),
        }
        return children
