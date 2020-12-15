from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.input.thermal.series.area.thermal.series import (
    InputThermalSeriesAreaThermalSeries,
)


class InputThermalSeriesAreaThermal(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            "series": InputThermalSeriesAreaThermalSeries(
                config.next_file("series.txt")
            ),
        }
        return children
