from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.output.simulation.ts_numbers.wind.area import (
    OutputSimulationTsNumbersWindArea,
)


class OutputSimulationTsNumbersWind(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            area: OutputSimulationTsNumbersWindArea(
                config.next_file(area + ".txt")
            )
            for area in config.area_names()
        }
        return children
