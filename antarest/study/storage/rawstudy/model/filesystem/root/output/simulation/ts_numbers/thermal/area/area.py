from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.ts_numbers.thermal.area.thermal import (
    OutputSimulationTsNumbersThermalAreaThermal,
)


class OutputSimulationTsNumbersThermalArea(FolderNode):
    def __init__(
        self, context: ContextServer, config: FileStudyTreeConfig, area: str
    ):
        FolderNode.__init__(self, context, config)
        self.area = area

    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            thermal: OutputSimulationTsNumbersThermalAreaThermal(
                self.context, config.next_file(thermal + ".txt")
            )
            for thermal in config.get_thermal_names(self.area)
        }
        return children
