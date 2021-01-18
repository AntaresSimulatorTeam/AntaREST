from api_iso_antares.filesystem.config.model import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.output.simulation.mode.mcind.scn.areas.areas import (
    OutputSimulationModeMcIndScnAreas,
)
from api_iso_antares.filesystem.root.output.simulation.mode.mcind.scn.links.links import (
    OutputSimulationModeMcIndScnLinks,
)


class OutputSimulationModeMcIndScn(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            "areas": OutputSimulationModeMcIndScnAreas(
                config.next_file("areas")
            ),
            "links": OutputSimulationModeMcIndScnLinks(
                config.next_file("links")
            ),
        }
        return children
