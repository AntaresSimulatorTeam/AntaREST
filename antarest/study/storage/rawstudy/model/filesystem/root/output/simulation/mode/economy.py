from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
    Simulation,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcall.mcall import (
    OutputSimulationModeMcAll,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcind.mcind import (
    OutputSimulationModeMcInd,
)


class OutputSimulationMode(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        simulation: Simulation,
    ):
        FolderNode.__init__(self, context, config)
        self.simulation = simulation

    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {}

        if self.simulation.by_year:
            children["mc-ind"] = OutputSimulationModeMcInd(
                self.context, config.next_file("mc-ind"), self.simulation
            )
        if self.simulation.synthesis:
            children["mc-all"] = OutputSimulationModeMcAll(
                self.context, config.next_file("mc-all")
            )

        return children
