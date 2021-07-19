from antarest.storage.repository.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.output.simulation.ts_numbers.solar.area import (
    OutputSimulationTsNumbersSolarArea,
)


class OutputSimulationTsNumbersSolar(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            area: OutputSimulationTsNumbersSolarArea(
                self.context, config.next_file(area + ".txt")
            )
            for area in config.area_names()
        }
        return children
