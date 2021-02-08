from antarest.storage.filesystem.config.model import StudyConfig
from antarest.storage.filesystem.folder_node import FolderNode
from antarest.storage.filesystem.inode import TREE
from antarest.storage.filesystem.root.output.simulation.ts_numbers.load.area import (
    OutputSimulationTsNumbersLoadArea,
)


class OutputSimulationTsNumbersLoad(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            area: OutputSimulationTsNumbersLoadArea(
                config.next_file(area + ".txt")
            )
            for area in config.area_names()
        }
        return children
