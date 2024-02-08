from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import InputSeriesMatrix
from antarest.study.storage.rawstudy.model.filesystem.matrix.matrix import MatrixFrequency


class InputThermalPreproAreaThermal(FolderNode):
    """
    Folder containing thermal cluster data: `input/thermal/prepro/{area_id}/{cluster_id}`.

    This folder contains the following files:

    - `data.txt` (matrix): TS Generator matrix (daily)
    - `modulation.txt` (matrix): Modulation matrix (hourly)
    """

    def build(self) -> TREE:
        children: TREE = {
            "data": InputSeriesMatrix(self.context, self.config.next_file("data.txt"), freq=MatrixFrequency.DAILY),
            "modulation": InputSeriesMatrix(self.context, self.config.next_file("modulation.txt")),
        }
        return children
