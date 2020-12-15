from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.output.simulation.economy.mcall.grid.areas import (
    OutputSimulationEconomyMcAllGridAreas,
)
from api_iso_antares.filesystem.root.output.simulation.economy.mcall.grid.digest import (
    OutputSimulationEconomyMcAllGridDigest,
)
from api_iso_antares.filesystem.root.output.simulation.economy.mcall.grid.links import (
    OutputSimulationEconomyMcAllGridLinks,
)
from api_iso_antares.filesystem.root.output.simulation.economy.mcall.grid.thermals import (
    OutputSimulationEconomyMcAllGridThermals,
)


class OutputSimulationEconomyMcAllGrid(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            "areas": OutputSimulationEconomyMcAllGridAreas(
                config.next_file("areas.txt")
            ),
            "digest": OutputSimulationEconomyMcAllGridDigest(
                config.next_file("digest.txt")
            ),
            "links": OutputSimulationEconomyMcAllGridLinks(
                config.next_file("links.txt")
            ),
            "thermal": OutputSimulationEconomyMcAllGridThermals(
                config.next_file("thermal.txt")
            ),
        }
        return children
