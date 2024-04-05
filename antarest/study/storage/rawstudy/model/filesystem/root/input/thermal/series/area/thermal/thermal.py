from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.constants import default_scenario_hourly
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency


class InputThermalSeriesAreaThermal(FolderNode):
    def build(self) -> TREE:
        children: TREE = {
            "series": InputSeriesMatrix(
                self.context,
                self.config.next_file("series.txt"),
                default_empty=default_scenario_hourly,
            ),
        }
        if self.config.version >= 870:
            children["CO2Cost"] = InputSeriesMatrix(
                self.context,
                self.config.next_file("CO2Cost.txt"),
                freq=MatrixFrequency.HOURLY,
                default_empty=default_scenario_hourly,
            )
            children["fuelCost"] = InputSeriesMatrix(
                self.context,
                self.config.next_file("fuelCost.txt"),
                freq=MatrixFrequency.HOURLY,
                default_empty=default_scenario_hourly,
            )
        return children
