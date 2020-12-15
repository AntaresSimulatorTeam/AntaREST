from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.output.simulation.adequacy.mcall.areas.areas import (
    OutputSimulationAdequacyMcAllAreas,
)
from api_iso_antares.filesystem.root.output.simulation.adequacy.mcall.grid.grid import (
    OutputSimulationAdequacyMcAllGrid,
)
from api_iso_antares.filesystem.root.output.simulation.adequacy.mcall.links.links import (
    OutputSimulationAdequacyMcAllLinks,
)


class OutputSimulationAdequacyMcAll(FolderNode):
    def __init__(self, config: Config):
        children: TREE = {
            "areas": OutputSimulationAdequacyMcAllAreas(
                config.next_file("areas")
            ),
            "grid": OutputSimulationAdequacyMcAllGrid(
                config.next_file("grid")
            ),
            "links": OutputSimulationAdequacyMcAllLinks(
                config.next_file("links")
            ),
        }
        FolderNode.__init__(self, config, children)
