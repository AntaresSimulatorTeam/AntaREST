from api_iso_antares.filesystem.config.model import Config, Simulation
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.output.simulation.economy.mcind.scn.scn import (
    OutputSimulationEconomyMcIndScn,
)


class OutputSimulationEconomyMcInd(FolderNode):
    def __init__(self, config: Config, simulation: Simulation):
        FolderNode.__init__(self, config)
        self.simulation = simulation

    def build(self, config: Config) -> TREE:
        children: TREE = {
            str("{:05d}".format(scn)): OutputSimulationEconomyMcIndScn(
                config.next_file("{:05d}".format(scn))
            )
            for scn in range(1, self.simulation.nbyears + 1)
        }
        return children
