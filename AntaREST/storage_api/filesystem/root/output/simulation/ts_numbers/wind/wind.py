from AntaREST.storage_api.filesystem.config.model import Config
from AntaREST.storage_api.filesystem.folder_node import FolderNode
from AntaREST.storage_api.filesystem.inode import TREE
from AntaREST.storage_api.filesystem.root.output.simulation.ts_numbers.wind.area import (
    OutputSimulationTsNumbersWindArea,
)


class OutputSimulationTsNumbersWind(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            area: OutputSimulationTsNumbersWindArea(
                config.next_file(area + ".txt")
            )
            for area in config.area_names()
        }
        return children
