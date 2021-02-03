from antarest.storage_api.filesystem.config.model import StudyConfig
from antarest.storage_api.filesystem.folder_node import FolderNode
from antarest.storage_api.filesystem.inode import TREE
from antarest.storage_api.filesystem.root.input.thermal.prepro.area.thermal.data import (
    InputThermalPreproAreaThermalData,
)
from antarest.storage_api.filesystem.root.input.thermal.prepro.area.thermal.modulation import (
    InputThermalPreproAreaThermalModulation,
)


class InputThermalPreproAreaThermal(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            "data": InputThermalPreproAreaThermalData(
                config.next_file("data.txt")
            ),
            "modulation": InputThermalPreproAreaThermalModulation(
                config.next_file("modulation.txt")
            ),
        }
        return children
