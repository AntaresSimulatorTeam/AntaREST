from antarest.storage_api.filesystem.config.model import (
    StudyConfig,
    Simulation,
)
from antarest.storage_api.filesystem.folder_node import FolderNode
from antarest.storage_api.filesystem.inode import TREE
from antarest.storage_api.filesystem.root.output.simulation.mode.mcind.scn.scn import (
    OutputSimulationModeMcIndScn,
)


class OutputSimulationModeMcInd(FolderNode):
    def __init__(self, config: StudyConfig, simulation: Simulation):
        FolderNode.__init__(self, config)
        self.simulation = simulation

    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            str("{:05d}".format(scn)): OutputSimulationModeMcIndScn(
                config.next_file("{:05d}".format(scn))
            )
            for scn in range(1, self.simulation.nbyears + 1)
        }
        return children
