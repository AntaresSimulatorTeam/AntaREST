from storage_api.filesystem.config.model import Config, Simulation
from storage_api.filesystem.folder_node import FolderNode
from storage_api.filesystem.inode import TREE
from storage_api.filesystem.root.output.simulation.mode.mcall.mcall import (
    OutputSimulationModeMcAll,
)
from storage_api.filesystem.root.output.simulation.mode.mcind.mcind import (
    OutputSimulationModeMcInd,
)


class OutputSimulationMode(FolderNode):
    def __init__(self, config: Config, simulation: Simulation):
        FolderNode.__init__(self, config)
        self.simulation = simulation

    def build(self, config: Config) -> TREE:
        children: TREE = {}

        if self.simulation.by_year:
            children["mc-ind"] = OutputSimulationModeMcInd(
                config.next_file("mc-ind"), self.simulation
            )
        if self.simulation.synthesis:
            children["mc-all"] = OutputSimulationModeMcAll(
                config.next_file("mc-all")
            )

        return children
