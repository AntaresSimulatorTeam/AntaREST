from antarest.storage.repository.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.output.simulation.ts_numbers.thermal.area.area import (
    OutputSimulationTsNumbersThermalArea,
)


class OutputSimulationTsNumbersThermal(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            area: OutputSimulationTsNumbersThermalArea(
                self.context, config.next_file(area), area
            )
            for area in config.area_names()
        }
        return children
