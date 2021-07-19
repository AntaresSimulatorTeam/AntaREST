from antarest.storage.business.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.business.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.storage.business.rawstudy.model.filesystem.inode import TREE
from antarest.storage.business.rawstudy.model.filesystem.root.output.simulation.ts_numbers.thermal.area.area import (
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
