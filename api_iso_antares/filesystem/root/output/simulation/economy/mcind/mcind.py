from api_iso_antares.filesystem.config import Config, Simulation
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.output.simulation.economy.mcind.scn.scn import (
    OutputSimulationEconomyMcIndScn,
)


class OutputSimulationEconomyMcInd(FolderNode):
    def __init__(self, config: Config, simulation: Simulation):
        children: TREE = {
            str("{:05d}".format(scn)): OutputSimulationEconomyMcIndScn(
                config.next_file("{:05d}".format(scn))
            )
            for scn in range(1, simulation.nbyears + 1)
        }
        FolderNode.__init__(self, config, children)
