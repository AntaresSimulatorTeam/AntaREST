from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import (
    InputSeriesMatrix,
)
from antarest.study.storage.variantstudy.business.matrix_constants.st_storage import (
    series,
)


class InputShortTermStorageAreaStorage(FolderNode):
    def build(self) -> TREE:
        children: TREE = {
            "PMAX-injection": InputSeriesMatrix(
                self.context,
                self.config.next_file("PMAX-injection.txt"),
                default_empty=series.pmax_injection.tolist(),
            ),
            "PMAX-withdrawal": InputSeriesMatrix(
                self.context,
                self.config.next_file("PMAX-withdrawal.txt"),
                default_empty=series.pmax_withdrawal.tolist(),
            ),
            "inflow": InputSeriesMatrix(
                self.context,
                self.config.next_file("inflow.txt"),
                default_empty=series.inflow.tolist(),
            ),
            "lower-rule-curve": InputSeriesMatrix(
                self.context,
                self.config.next_file("lower-rule-curve.txt"),
                default_empty=series.lower_rule_curve.tolist(),
            ),
            "upper-rule-curve": InputSeriesMatrix(
                self.context,
                self.config.next_file("upper-rule-curve.txt"),
                default_empty=series.upper_rule_curve.tolist(),
            ),
        }
        return children
