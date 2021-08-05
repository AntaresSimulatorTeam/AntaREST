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


class InputLoad(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            "prepro": InputPrepro(self.context, config.next_file("prepro")),
            "series": AreaMatrixList(
                self.context, config.next_file("series"), "load_"
            ),
        }
        return children
