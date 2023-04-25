from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.constants import (
    default_scenario_hourly,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import (
    InputSeriesMatrix,
)


class InputShortTermStorageAreaStorage(FolderNode):
    def build(self) -> TREE:
        children: TREE = {
            "PMAX-injection": InputSeriesMatrix(
                self.context, self.config.next_file("PMAX-injection.txt")
            ),
            "PMAX-withdrawal": InputSeriesMatrix(
                self.context, self.config.next_file("PMAX-withdrawal.txt")
            ),
            "inflow": InputSeriesMatrix(
                self.context, self.config.next_file("inflow.txt")
            ),
            "lower-rule-curve": InputSeriesMatrix(
                self.context, self.config.next_file("lower-rule-curve.txt")
            ),
            "upper-rule-curve": InputSeriesMatrix(
                self.context, self.config.next_file("upper-rule-curve.txt")
            ),
        }
        return children
