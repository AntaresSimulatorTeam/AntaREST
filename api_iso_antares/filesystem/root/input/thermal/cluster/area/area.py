from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.input.thermal.cluster.area.list import (
    InputThermalClustersAreaList,
)


class InputThermalClustersArea(FolderNode):
    def __init__(self, config: Config, area: str):
        FolderNode.__init__(self, config)
        self.area = area

    def build(self, config: Config) -> TREE:
        children: TREE = {
            "list": InputThermalClustersAreaList(
                config.next_file("list.ini"), self.area
            )
        }
        return children
