from antarest.storage.repository.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.input.thermal.prepro.area.thermal.data import (
    InputThermalPreproAreaThermalData,
)
from antarest.storage.repository.filesystem.root.input.thermal.prepro.area.thermal.modulation import (
    InputThermalPreproAreaThermalModulation,
)


class InputThermalPreproAreaThermal(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            "data": InputThermalPreproAreaThermalData(
                self.context, config.next_file("data.txt")
            ),
            "modulation": InputThermalPreproAreaThermalModulation(
                self.context, config.next_file("modulation.txt")
            ),
        }
        return children
