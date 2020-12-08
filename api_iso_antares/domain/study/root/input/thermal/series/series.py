from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.folder_node import FolderNode
from api_iso_antares.domain.study.inode import TREE
from api_iso_antares.domain.study.root.input.thermal.series.area.area import (
    InputThermalSeriesArea,
)


class InputThermalSeries(FolderNode):
    def __init__(self, config: Config):
        children: TREE = {
            a: InputThermalSeriesArea(config.next_file(a), area=a)
            for a in config.area_names
        }
        FolderNode.__init__(self, children)
