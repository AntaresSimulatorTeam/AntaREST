from api_iso_antares.filesystem.config.model import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.output.simulation.adequacy.mcind.scn.areas.areas import (
    OutputSimulationAdequacyMcIndScnAreas,
)
from api_iso_antares.filesystem.root.output.simulation.adequacy.mcind.scn.links.links import (
    OutputSimulationAdequacyMcIndScnLinks,
)


class OutputSimulationAdequacyMcIndScn(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            "areas": OutputSimulationAdequacyMcIndScnAreas(
                config.next_file("areas")
            ),
            "links": OutputSimulationAdequacyMcIndScnLinks(
                config.next_file("links")
            ),
        }
        return children
