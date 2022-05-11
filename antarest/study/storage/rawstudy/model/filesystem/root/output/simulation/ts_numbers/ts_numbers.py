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
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.ts_numbers.ts_numbers_data import (
    TsNumberVector,
)


class OutputSimulationTsNumbers(FolderNode):
    def build(self) -> TREE:
        children: TREE = {
            "hydro": AreaMatrixList(
                self.context,
                self.config.next_file("hydro"),
                matrix_class=TsNumberVector,
            ),
            "load": AreaMatrixList(
                self.context,
                self.config.next_file("load"),
                matrix_class=TsNumberVector,
            ),
            "solar": AreaMatrixList(
                self.context,
                self.config.next_file("solar"),
                matrix_class=TsNumberVector,
            ),
            "wind": AreaMatrixList(
                self.context,
                self.config.next_file("wind"),
                matrix_class=TsNumberVector,
            ),
            "thermal": AreaMultipleMatrixList(
                self.context,
                self.config.next_file("thermal"),
                ThermalMatrixList,
                TsNumberVector,
            ),
        }
        return children
