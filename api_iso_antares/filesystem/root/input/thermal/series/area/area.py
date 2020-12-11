from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.input.thermal.series.area.thermal.thermal import (
    InputThermalSeriesAreaThermal,
)


class InputThermalSeriesArea(FolderNode):
    def __init__(self, config: Config, area: str):
        children: TREE = {
            ther: InputThermalSeriesAreaThermal(config.next_file(ther))
            for ther in config.get_thermals(area)
        }
        FolderNode.__init__(self, config, children)
