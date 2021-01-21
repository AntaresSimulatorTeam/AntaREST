from storage_api.filesystem.config.model import Config
from storage_api.filesystem.folder_node import FolderNode
from storage_api.filesystem.inode import TREE
from storage_api.filesystem.root.input.thermal.prepro.area.thermal.data import (
    InputThermalPreproAreaThermalData,
)
from storage_api.filesystem.root.input.thermal.prepro.area.thermal.modulation import (
    InputThermalPreproAreaThermalModulation,
)


class InputThermalPreproAreaThermal(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            "data": InputThermalPreproAreaThermalData(
                config.next_file("data.txt")
            ),
            "modulation": InputThermalPreproAreaThermalModulation(
                config.next_file("modulation.txt")
            ),
        }
        return children
