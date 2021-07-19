from antarest.storage.repository.filesystem.config.model import (
    FileStudyTreeConfig,
    Simulation,
)
from antarest.storage.repository.filesystem.context import ContextServer
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.output.simulation.mode.mcind.scn.scn import (
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

    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            str("{:05d}".format(scn)): OutputSimulationModeMcIndScn(
                self.context, config.next_file("{:05d}".format(scn))
            )
            for scn in range(1, self.simulation.nbyears + 1)
        }
        return children
