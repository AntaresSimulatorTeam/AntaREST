from antarest.study.storage.rawstudy.model.filesystem.common.area_matrix_list import (
    AreaMatrixList,
    AreaMultipleMatrixList,
    ThermalMatrixList,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.raw_file_node import (
    RawFileNode,
)


class OutputSimulationTsNumbers(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            "hydro": AreaMatrixList(
                self.context,
                config.next_file("hydro"),
                matrix_class=RawFileNode,
            ),
            "load": AreaMatrixList(
                self.context,
                config.next_file("load"),
                matrix_class=RawFileNode,
            ),
            "solar": AreaMatrixList(
                self.context,
                config.next_file("solar"),
                matrix_class=RawFileNode,
            ),
            "wind": AreaMatrixList(
                self.context,
                config.next_file("wind"),
                matrix_class=RawFileNode,
            ),
            "thermal": AreaMultipleMatrixList(
                self.context,
                config.next_file("thermal"),
                ThermalMatrixList,
                RawFileNode,
            ),
        }
        return children
