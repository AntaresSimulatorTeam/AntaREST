from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.output.simulation.ts_numbers.hydro.area import (
    OutputSimulationTsNumbersHydroArea,
)


class OutputSimulationTsNumbersHydro(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            area: OutputSimulationTsNumbersHydroArea(
                self.context, config.next_file(area + ".txt")
            )
            for area in config.area_names()
        }
        return children
