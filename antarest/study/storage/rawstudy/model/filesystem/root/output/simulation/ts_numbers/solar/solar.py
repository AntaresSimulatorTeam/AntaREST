from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.ts_numbers.solar.area import (
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
