from storage_api.filesystem.config.model import Config
from storage_api.filesystem.folder_node import FolderNode
from storage_api.filesystem.inode import TREE
from storage_api.filesystem.root.output.simulation.ts_numbers.thermal.area.area import (
    OutputSimulationTsNumbersThermalArea,
)


class OutputSimulationTsNumbersThermal(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            area: OutputSimulationTsNumbersThermalArea(
                config.next_file(area), area
            )
            for area in config.area_names()
        }
        return children
