from api_iso_antares.filesystem.config import Config, Simulation
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.output.simulation.adequacy.mcall.mcall import (
    OutputSimulationAdequacyMcAll,
)


class OutputSimulationAdequacy(FolderNode):
    def __init__(self, config: Config, simulation: Simulation):
        children: TREE = {
            "mc-all": OutputSimulationAdequacyMcAll(
                config.next_file("mc-all")
            ),
        }
        FolderNode.__init__(self, config, children)
