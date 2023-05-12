from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.constants import (
    default_scenario_daily,
    default_scenario_hourly,
    default_scenario_monthly,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import (
    InputSeriesMatrix,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import (
    MatrixFrequency,
)


class InputHydroSeriesArea(FolderNode):
    def build(self) -> TREE:
        freq = (
            MatrixFrequency.DAILY
            if self.config.version >= 650
            else MatrixFrequency.MONTHLY
        )
        default_empty = (
            default_scenario_daily
            if self.config.version >= 650
            else default_scenario_monthly
        )
        return {
            "mod": InputSeriesMatrix(
                self.context,
                self.config.next_file("mod.txt"),
                freq=freq,
                default_empty=default_empty,
            ),
            # Run of River
            "ror": InputSeriesMatrix(
                self.context,
                self.config.next_file("ror.txt"),
                freq=MatrixFrequency.HOURLY,
                default_empty=default_scenario_hourly,
            ),
        }
