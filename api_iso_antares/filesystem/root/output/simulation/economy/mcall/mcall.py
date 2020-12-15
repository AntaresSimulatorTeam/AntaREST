from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.output.simulation.economy.mcall.areas.areas import (
    OutputSimulationEconomyMcAllAreas,
)
from api_iso_antares.filesystem.root.output.simulation.economy.mcall.grid.grid import (
    OutputSimulationEconomyMcAllGrid,
)
from api_iso_antares.filesystem.root.output.simulation.economy.mcall.links.links import (
    OutputSimulationEconomyMcAllLinks,
)


class OutputSimulationEconomyMcAll(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            "areas": OutputSimulationEconomyMcAllAreas(
                config.next_file("areas")
            ),
            "grid": OutputSimulationEconomyMcAllGrid(config.next_file("grid")),
            "links": OutputSimulationEconomyMcAllLinks(
                config.next_file("links")
            ),
        }
        return children
