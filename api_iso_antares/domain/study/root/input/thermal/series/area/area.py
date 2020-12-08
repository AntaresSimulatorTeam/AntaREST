from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.folder_node import FolderNode
from api_iso_antares.domain.study.inode import TREE
from api_iso_antares.domain.study.root.input.thermal.series.area.thermal.thermal import (
    InputThermalSeriesAreaThermal,
)


class InputThermalSeriesArea(FolderNode):
    def __init__(self, config: Config, area: str):
        children: TREE = {
            ther: InputThermalSeriesAreaThermal(config.next_file(ther))
            for ther in config.get_thermals(area)
        }
        FolderNode.__init__(self, children)
