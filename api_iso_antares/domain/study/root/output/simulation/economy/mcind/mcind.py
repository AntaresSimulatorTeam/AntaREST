from api_iso_antares.domain.study.config import Config, Simulation
from api_iso_antares.domain.study.folder_node import FolderNode
from api_iso_antares.domain.study.inode import TREE
from api_iso_antares.domain.study.root.output.simulation.economy.mcind.scn.scn import (
    OutputSimulationEconomyMcIndScn,
)


class OutputSimulationEconomyMcInd(FolderNode):
    def __init__(self, config: Config, simulation: Simulation):
        children: TREE = {
            str(scn): OutputSimulationEconomyMcIndScn(
                config.next_file("{:05d}".format(scn))
            )
            for scn in range(1, simulation.nbyears + 1)
        }
        FolderNode.__init__(self, children)
