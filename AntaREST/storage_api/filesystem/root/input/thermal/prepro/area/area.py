from AntaREST.storage_api.filesystem.config.model import Config
from AntaREST.storage_api.filesystem.folder_node import FolderNode
from AntaREST.storage_api.filesystem.inode import TREE
from AntaREST.storage_api.filesystem.root.input.thermal.prepro.area.thermal.thermal import (
    InputThermalPreproAreaThermal,
)


class InputThermalPreproArea(FolderNode):
    def __init__(self, config: Config, area: str):
        FolderNode.__init__(self, config)
        self.area = area

    def build(self, config: Config) -> TREE:
        children: TREE = {
            ther: InputThermalPreproAreaThermal(config.next_file(ther))
            for ther in config.get_thermals(self.area)
        }
        return children
