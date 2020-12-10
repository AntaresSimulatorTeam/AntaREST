from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.output.simulation.ts_numbers.thermal.area.thermal import (
    OutputSimulationTsNumbersThermalAreaThermal,
)


class OutputSimulationTsNumbersThermalArea(FolderNode):
    def __init__(self, config: Config, area: str):
        children: TREE = {
            thermal: OutputSimulationTsNumbersThermalAreaThermal(
                config.next_file(thermal + ".txt")
            )
            for thermal in config.get_thermals(area)
        }
        FolderNode.__init__(self, config, children)
