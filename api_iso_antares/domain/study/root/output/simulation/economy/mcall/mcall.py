from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.folder_node import FolderNode
from api_iso_antares.domain.study.inode import TREE
from api_iso_antares.domain.study.root.output.simulation.economy.mcall.areas.areas import (
    OutputSimulationEconomyMcAllAreas,
)
from api_iso_antares.domain.study.root.output.simulation.economy.mcall.grid.grid import (
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
