from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
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
    def __init__(self, config: Config):
        children = {
            "areas": OutputSimulationEconomyMcAllGridAreas(
                config.next_file("areas.txt")
            ),
            "digest": OutputSimulationEconomyMcAllGridDigest(
                config.next_file("digest.txt")
            ),
            "links": OutputSimulationEconomyMcAllGridLinks(
                config.next_file("links.txt")
            ),
            "thermals": OutputSimulationEconomyMcAllGridThermals(
                config.next_file("thermals.txt")
            ),
        }
        FolderNode.__init__(self, config, children)
