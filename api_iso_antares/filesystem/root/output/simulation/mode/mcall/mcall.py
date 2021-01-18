from api_iso_antares.filesystem.config.model import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.output.simulation.mode.mcall.areas.areas import (
    OutputSimulationModeMcAllAreas,
)
from api_iso_antares.filesystem.root.output.simulation.mode.mcall.grid.grid import (
    OutputSimulationModeMcAllGrid,
)
from api_iso_antares.filesystem.root.output.simulation.mode.mcall.links.links import (
    OutputSimulationModeMcAllLinks,
)


class OutputSimulationModeMcAll(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            "areas": OutputSimulationModeMcAllAreas(config.next_file("areas")),
            "grid": OutputSimulationModeMcAllGrid(config.next_file("grid")),
            "links": OutputSimulationModeMcAllLinks(config.next_file("links")),
        }
        return children
