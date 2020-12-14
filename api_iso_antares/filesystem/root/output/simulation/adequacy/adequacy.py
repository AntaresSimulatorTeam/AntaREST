from api_iso_antares.filesystem.config import Config, Simulation
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.output.simulation.adequacy.mcall.mcall import (
    OutputSimulationAdequacyMcAll,
)
from api_iso_antares.filesystem.root.output.simulation.adequacy.mcind.mcind import (
    OutputSimulationAdequacyMcInd,
)


class OutputSimulationAdequacy(FolderNode):
    def __init__(self, config: Config, simulation: Simulation):
        children: TREE = {}

        if simulation.by_year:
            children["mc-ind"] = OutputSimulationAdequacyMcInd(
                config.next_file("mc-ind"), simulation
            )
        if simulation.synthesis:
            children["mc-all"] = OutputSimulationAdequacyMcAll(
                config.next_file("mc-all")
            )
        FolderNode.__init__(self, config, children)
