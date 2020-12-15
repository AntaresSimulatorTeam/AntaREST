from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.input.solar.series.area import (
    InputSolarSeriesArea,
)


class InputSolarSeries(FolderNode):
    def __init__(self, config: Config):
        children: TREE = {
            f"solar_{a}": InputSolarSeriesArea(
                config.next_file(f"solar_{a}.txt")
            )
            for a in config.area_names
        }
        FolderNode.__init__(self, config, children)
