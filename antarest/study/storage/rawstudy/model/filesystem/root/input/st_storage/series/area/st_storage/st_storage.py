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


class InputSTStorageAreaStorage(FolderNode):
    def build(self) -> TREE:
        children: TREE = {
            "PMAX-injection": InputSeriesMatrix(
                self.context,
                self.config.next_file("PMAX-injection.txt"),
                default_empty=series.pmax_injection,
            ),
            "PMAX-withdrawal": InputSeriesMatrix(
                self.context,
                self.config.next_file("PMAX-withdrawal.txt"),
                default_empty=series.pmax_withdrawal,
            ),
            "inflows": InputSeriesMatrix(
                self.context,
                self.config.next_file("inflows.txt"),
                default_empty=series.inflows,
            ),
            "lower-rule-curve": InputSeriesMatrix(
                self.context,
                self.config.next_file("lower-rule-curve.txt"),
                default_empty=series.lower_rule_curve,
            ),
            "upper-rule-curve": InputSeriesMatrix(
                self.context,
                self.config.next_file("upper-rule-curve.txt"),
                default_empty=series.upper_rule_curve,
            ),
        }
        return children
