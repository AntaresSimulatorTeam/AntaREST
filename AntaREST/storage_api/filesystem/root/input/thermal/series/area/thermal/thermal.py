from AntaREST.storage_api.filesystem.config.model import Config
from AntaREST.storage_api.filesystem.folder_node import FolderNode
from AntaREST.storage_api.filesystem.inode import TREE
from AntaREST.storage_api.filesystem.root.input.thermal.series.area.thermal.series import (
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
