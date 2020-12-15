from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.output.simulation.adequacy.mcind.scn.areas.areas import (
    OutputSimulationAdequacyMcIndScnAreas,
)
from api_iso_antares.filesystem.root.output.simulation.adequacy.mcind.scn.links.links import (
    OutputSimulationAdequacyMcIndScnLinks,
)


class OutputSimulationAdequacyMcIndScn(FolderNode):
    def __init__(self, config: Config):
        children: TREE = {
            "areas": OutputSimulationAdequacyMcIndScnAreas(
                config.next_file("areas")
            ),
            "links": OutputSimulationAdequacyMcIndScnLinks(
                config.next_file("links")
            ),
        }
        FolderNode.__init__(self, config, children)
