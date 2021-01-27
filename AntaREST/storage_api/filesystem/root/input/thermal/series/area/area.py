from AntaREST.storage_api.filesystem.config.model import Config
from AntaREST.storage_api.filesystem.folder_node import FolderNode
from AntaREST.storage_api.filesystem.inode import TREE
from AntaREST.storage_api.filesystem.root.input.thermal.series.area.thermal.thermal import (
    InputThermalSeriesAreaThermal,
)


class InputThermalSeriesArea(FolderNode):
    def __init__(self, config: Config, area: str):
        FolderNode.__init__(self, config)
        self.area = area

    def build(self, config: Config) -> TREE:
        children: TREE = {
            ther: InputThermalSeriesAreaThermal(config.next_file(ther))
            for ther in config.get_thermals(self.area)
        }
        return children
