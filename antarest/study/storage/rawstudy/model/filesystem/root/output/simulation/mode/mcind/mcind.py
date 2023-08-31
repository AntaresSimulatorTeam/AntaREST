from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfig, Simulation
from antarest.study.storage.rawstudy.model.filesystem.context import ContextServer
from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcind.scn import (
    OutputSimulationModeMcIndScn,
)


class OutputSimulationModeMcInd(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        simulation: Simulation,
    ):
        FolderNode.__init__(self, context, config)
        self.simulation = simulation

    def build(self) -> TREE:
        children: TREE = {
            str("{:05d}".format(scn)): OutputSimulationModeMcIndScn(
                self.context, self.config.next_file("{:05d}".format(scn))
            )
            for scn in self.simulation.playlist or range(1, self.simulation.nbyears + 1)
        }
        return children
