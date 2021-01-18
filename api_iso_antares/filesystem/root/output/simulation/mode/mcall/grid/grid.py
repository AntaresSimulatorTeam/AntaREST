from api_iso_antares.filesystem.config.model import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.output.simulation.mode.mcall.grid.areas import (
    OutputSimulationModeMcAllGridAreas,
)
from api_iso_antares.filesystem.root.output.simulation.mode.mcall.grid.digest import (
    OutputSimulationModeMcAllGridDigest,
)
from api_iso_antares.filesystem.root.output.simulation.mode.mcall.grid.links import (
    OutputSimulationModeMcAllGridLinks,
)
from api_iso_antares.filesystem.root.output.simulation.mode.mcall.grid.thermals import (
    OutputSimulationModeMcAllGridThermals,
)


class OutputSimulationModeMcAllGrid(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            "areas": OutputSimulationModeMcAllGridAreas(
                config.next_file("areas.txt")
            ),
            "digest": OutputSimulationModeMcAllGridDigest(
                config.next_file("digest.txt")
            ),
            "links": OutputSimulationModeMcAllGridLinks(
                config.next_file("links.txt")
            ),
            "thermal": OutputSimulationModeMcAllGridThermals(
                config.next_file("thermal.txt")
            ),
        }
        return children
