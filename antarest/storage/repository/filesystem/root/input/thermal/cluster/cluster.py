from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.input.thermal.cluster.area.area import (
    InputThermalClustersArea,
)


class InputThermalClusters(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            a: InputThermalClustersArea(config.next_file(a), area=a)
            for a in config.area_names()
        }
        return children
