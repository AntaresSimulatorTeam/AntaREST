from api_iso_antares.filesystem.config.model import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.output.simulation.ts_numbers.hydro.area import (
    OutputSimulationTsNumbersHydroArea,
)


class OutputSimulationTsNumbersHydro(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            area: OutputSimulationTsNumbersHydroArea(
                config.next_file(area + ".txt")
            )
            for area in config.area_names()
        }
        return children
