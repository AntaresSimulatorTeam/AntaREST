from antarest.storage_api.filesystem.config.model import Config
from antarest.storage_api.filesystem.folder_node import FolderNode
from antarest.storage_api.filesystem.inode import TREE
from antarest.storage_api.filesystem.root.output.simulation.ts_numbers.hydro.area import (
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
