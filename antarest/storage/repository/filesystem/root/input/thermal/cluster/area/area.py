from antarest.storage.repository.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.repository.filesystem.context import ContextServer
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.input.thermal.cluster.area.list import (
    InputThermalClustersAreaList,
)


class InputThermalClustersArea(FolderNode):
    def __init__(
        self, context: ContextServer, config: FileStudyTreeConfig, area: str
    ):
        FolderNode.__init__(self, context, config)
        self.area = area

    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            "list": InputThermalClustersAreaList(
                self.context, config.next_file("list.ini"), self.area
            )
        }
        return children
