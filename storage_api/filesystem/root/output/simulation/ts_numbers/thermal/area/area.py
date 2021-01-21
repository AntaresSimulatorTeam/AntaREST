from storage_api.filesystem.config.model import Config
from storage_api.filesystem.folder_node import FolderNode
from storage_api.filesystem.inode import TREE
from storage_api.filesystem.root.output.simulation.ts_numbers.thermal.area.thermal import (
    OutputSimulationTsNumbersThermalAreaThermal,
)


class OutputSimulationTsNumbersThermalArea(FolderNode):
    def __init__(self, config: Config, area: str):
        FolderNode.__init__(self, config)
        self.area = area

    def build(self, config: Config) -> TREE:
        children: TREE = {
            thermal: OutputSimulationTsNumbersThermalAreaThermal(
                config.next_file(thermal + ".txt")
            )
            for thermal in config.get_thermals(self.area)
        }
        return children
