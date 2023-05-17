from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.constants import (
    default_8_fixed_hourly,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import (
    InputSeriesMatrix,
)


class InputMiscGen(FolderNode):
    def build(self) -> TREE:
        children: TREE = {
            f"miscgen-{a}": InputSeriesMatrix(
                self.context,
                self.config.next_file(f"miscgen-{a}.txt"),
                default_empty=default_8_fixed_hourly,
            )
            for a in self.config.area_names()
        }
        return children
