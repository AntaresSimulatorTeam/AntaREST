from api_iso_antares.filesystem.config import Config, Simulation
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.output.simulation.economy.mcall.mcall import (
    OutputSimulationEconomyMcAll,
)
from api_iso_antares.filesystem.root.output.simulation.economy.mcind.mcind import (
    OutputSimulationEconomyMcInd,
)


class OutputSimulationEconomy(FolderNode):
    def __init__(self, config: Config, simulation: Simulation):
        FolderNode.__init__(self, config)
        self.simulation = simulation

    def build(self, config: Config) -> TREE:
        children: TREE = {}

        if self.simulation.by_year:
            children["mc-ind"] = OutputSimulationEconomyMcInd(
                config.next_file("mc-ind"), self.simulation
            )
        if self.simulation.synthesis:
            children["mc-all"] = OutputSimulationEconomyMcAll(
                config.next_file("mc-all")
            )

        return children
