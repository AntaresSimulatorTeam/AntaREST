from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.output.simulation.economy.mcall.areas.areas import (
    OutputSimulationEconomyMcAllAreas,
)
from api_iso_antares.filesystem.root.output.simulation.economy.mcall.grid.grid import (
    OutputSimulationEconomyMcAllGrid,
)


class OutputSimulationEconomyMcAll(FolderNode):
    def __init__(self, config: Config):
        children: TREE = {
            "areas": OutputSimulationEconomyMcAllAreas(
                config.next_file("areas")
            ),
            "grid": OutputSimulationEconomyMcAllGrid(config.next_file("grid")),
        }
        FolderNode.__init__(self, children)
