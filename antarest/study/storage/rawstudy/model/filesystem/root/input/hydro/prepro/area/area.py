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
from antarest.study.storage.rawstudy.model.filesystem.raw_file_node import (
    RawFileNode,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.hydro.prepro.area.prepro import (
    InputHydroPreproAreaPrepro,
)


class InputHydroPreproArea(FolderNode):
    def build(self) -> TREE:
        children: TREE = {
            "energy": InputSeriesMatrix(
                self.context, self.config.next_file("energy.txt")
            ),
            "prepro": InputHydroPreproAreaPrepro(
                self.context, self.config.next_file("prepro.ini")
            ),
        }
        return children
