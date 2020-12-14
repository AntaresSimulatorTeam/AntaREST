from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.input.load.series.area import (
    InputLoadSeriesArea,
)


class InputLoadSeries(FolderNode):
    def __init__(self, config: Config):
        children: TREE = {
            f"load_{a}": InputLoadSeriesArea(config.next_file(f"load_{a}.txt"))
            for a in config.area_names
        }
        FolderNode.__init__(self, config, children)
