from antarest.storage.repository.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.input.thermal.series.area.thermal.series import (
    InputThermalSeriesAreaThermalSeries,
)


class InputThermalSeriesAreaThermal(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            "series": InputThermalSeriesAreaThermalSeries(
                self.context, config.next_file("series.txt")
            ),
        }
        return children
