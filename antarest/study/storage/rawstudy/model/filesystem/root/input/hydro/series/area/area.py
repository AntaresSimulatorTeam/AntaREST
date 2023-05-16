from typing import Dict, Any

from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE, INode
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
        hydro_series_matrices: Dict[str, INode[Any, Any, Any]] = {
            "mod": InputSeriesMatrix(
                self.context,
                self.config.next_file("mod.txt"),
                freq=freq,
                default_empty=default_empty.tolist(),
            ),
            # Run of River
            "ror": InputSeriesMatrix(
                self.context,
                self.config.next_file("ror.txt"),
                freq=MatrixFrequency.HOURLY,
                default_empty=default_scenario_hourly.tolist(),
            ),
        }
        if self.config.version >= 860:
            hydro_series_matrices["mingen"] = InputSeriesMatrix(
                self.context,
                self.config.next_file("mingen.txt"),
                freq=MatrixFrequency.HOURLY,
                default_empty=default_scenario_hourly.tolist(),
            )
        return hydro_series_matrices
