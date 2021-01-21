from storage_api.filesystem.config.model import Config
from storage_api.filesystem.folder_node import FolderNode
from storage_api.filesystem.inode import TREE
from storage_api.filesystem.root.output.simulation.mode.mcall.areas.areas import (
    OutputSimulationModeMcAllAreas,
)
from storage_api.filesystem.root.output.simulation.mode.mcall.grid.grid import (
    OutputSimulationModeMcAllGrid,
)
from storage_api.filesystem.root.output.simulation.mode.mcall.links.links import (
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
