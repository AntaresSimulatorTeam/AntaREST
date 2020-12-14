from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.output.simulation.adequacy.mcall.grid.areas import (
    OutputSimulationAdequacyMcAllGridAreas,
)
from api_iso_antares.filesystem.root.output.simulation.adequacy.mcall.grid.digest import (
    OutputSimulationAdequacyMcAllGridDigest,
)
from api_iso_antares.filesystem.root.output.simulation.adequacy.mcall.grid.links import (
    OutputSimulationAdequacyMcAllGridLinks,
)
from api_iso_antares.filesystem.root.output.simulation.adequacy.mcall.grid.thermals import (
    OutputSimulationAdequacyMcAllGridThermals,
)


class OutputSimulationAdequacyMcAllGrid(FolderNode):
    def __init__(self, config: Config):
        children: TREE = {
            "areas": OutputSimulationAdequacyMcAllGridAreas(
                config.next_file("areas.txt")
            ),
            "digest": OutputSimulationAdequacyMcAllGridDigest(
                config.next_file("digest.txt")
            ),
            "links": OutputSimulationAdequacyMcAllGridLinks(
                config.next_file("links.txt")
            ),
            "thermal": OutputSimulationAdequacyMcAllGridThermals(
                config.next_file("thermal.txt")
            ),
        }
        FolderNode.__init__(self, config, children)
