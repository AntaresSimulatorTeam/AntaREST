from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.input.thermal.prepro.area.thermal.thermal import (
    InputThermalPreproAreaThermal,
)


class InputThermalPreproArea(FolderNode):
    def __init__(self, config: Config, area: str):
        children: TREE = {
            ther: InputThermalPreproAreaThermal(config.next_file(ther))
            for ther in config.get_thermals(area)
        }
        FolderNode.__init__(self, config, children)
