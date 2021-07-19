from antarest.storage.repository.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.input.thermal.prepro.area.area import (
    InputThermalPreproArea,
)


class InputThermalPrepro(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            a: InputThermalPreproArea(
                self.context, config.next_file(a), area=a
            )
            for a in config.area_names()
        }
        return children
