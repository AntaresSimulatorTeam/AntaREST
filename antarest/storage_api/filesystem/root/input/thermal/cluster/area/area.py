from antarest.storage_api.filesystem.config.model import StudyConfig
from antarest.storage_api.filesystem.folder_node import FolderNode
from antarest.storage_api.filesystem.inode import TREE
from antarest.storage_api.filesystem.root.input.thermal.cluster.area.list import (
    InputThermalClustersAreaList,
)


class InputThermalClustersArea(FolderNode):
    def __init__(self, config: StudyConfig, area: str):
        FolderNode.__init__(self, config)
        self.area = area

    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            "list": InputThermalClustersAreaList(
                config.next_file("list.ini"), self.area
            )
        }
        return children
