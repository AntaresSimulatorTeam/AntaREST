from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.folder_node import FolderNode
from api_iso_antares.domain.study.inode import TREE
from api_iso_antares.domain.study.root.input.thermal.cluster.area.list import (
    InputThermalClustersAreaList,
)


class InputThermalClustersArea(FolderNode):
    def __init__(self, config: Config, area: str):
        children: TREE = {
            "list": InputThermalClustersAreaList(
                config.next_file("list.ini"), area
            )
        }
        FolderNode.__init__(self, children)
