from api_iso_antares.domain.study.config import Config, Simulation
from api_iso_antares.domain.study.folder_node import FolderNode
from api_iso_antares.domain.study.inode import TREE
from api_iso_antares.domain.study.root.output.simulation.economy.mcall.mcall import (
    OutputSimulationEconomyMcAll,
)
from api_iso_antares.domain.study.root.output.simulation.economy.mcind.mcind import (
    OutputSimulationEconomyMcInd,
)


class OutputSimulationEconomy(FolderNode):
    def __init__(self, config: Config, simulation: Simulation):
        children: TREE = {
            "mc-all": OutputSimulationEconomyMcAll(config.next_file("mc-all")),
            "mc-ind": OutputSimulationEconomyMcInd(
                config.next_file("mc-ind"), simulation
            ),
        }
        FolderNode.__init__(self, children)
