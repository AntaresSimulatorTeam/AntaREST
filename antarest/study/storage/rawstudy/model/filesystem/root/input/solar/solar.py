from antarest.study.storage.rawstudy.model.filesystem.common.area_matrix_list import (
    AreaMatrixList,
)
from antarest.study.storage.rawstudy.model.filesystem.common.prepro import (
    InputPrepro,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE


class InputSolar(FolderNode):
    def build(self) -> TREE:
        children: TREE = {
            "prepro": InputPrepro(
                self.context, self.config.next_file("prepro")
            ),
            "series": AreaMatrixList(
                self.context, self.config.next_file("series"), "solar_"
            ),
        }
        return children
