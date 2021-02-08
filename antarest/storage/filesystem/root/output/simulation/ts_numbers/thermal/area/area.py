from antarest.storage.filesystem.config.model import StudyConfig
from antarest.storage.filesystem.folder_node import FolderNode
from antarest.storage.filesystem.inode import TREE
from antarest.storage.filesystem.root.output.simulation.ts_numbers.thermal.area.thermal import (
    OutputSimulationTsNumbersThermalAreaThermal,
)


class OutputSimulationTsNumbersThermalArea(FolderNode):
    def __init__(self, config: StudyConfig, area: str):
        FolderNode.__init__(self, config)
        self.area = area

    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            thermal: OutputSimulationTsNumbersThermalAreaThermal(
                config.next_file(thermal + ".txt")
            )
            for thermal in config.get_thermals(self.area)
        }
        return children
