from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.folder_node import FolderNode
from api_iso_antares.domain.study.inode import TREE
from api_iso_antares.domain.study.root.input.thermal.prepro.area.thermal.data import (
    InputThermalPreproAreaThermalData,
)
from api_iso_antares.domain.study.root.input.thermal.prepro.area.thermal.modulation import (
    InputThermalPreproAreaThermalModulation,
)


class InputThermalPreproAreaThermal(FolderNode):
    def __init__(self, config: Config):
        children: TREE = {
            "data": InputThermalPreproAreaThermalData(
                config.next_file("data.txt")
            ),
            "modulation": InputThermalPreproAreaThermalModulation(
                config.next_file("modulation.txt")
            ),
        }
        FolderNode.__init__(self, children)
