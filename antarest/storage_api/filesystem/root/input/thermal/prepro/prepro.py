from antarest.storage_api.filesystem.config.model import Config
from antarest.storage_api.filesystem.folder_node import FolderNode
from antarest.storage_api.filesystem.inode import TREE
from antarest.storage_api.filesystem.root.input.thermal.prepro.area.area import (
    InputThermalPreproArea,
)


class InputThermalPrepro(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            a: InputThermalPreproArea(config.next_file(a), area=a)
            for a in config.area_names()
        }
        return children
