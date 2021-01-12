from api_iso_antares.filesystem.config.model import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.output.simulation.economy.mcind.scn.areas.areas import (
    OutputSimulationEconomyMcIndScnAreas,
)
from api_iso_antares.filesystem.root.output.simulation.economy.mcind.scn.links.links import (
    OutputSimulationEconomyMcIndScnLinks,
)


class OutputSimulationEconomyMcIndScn(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            "areas": OutputSimulationEconomyMcIndScnAreas(
                config.next_file("areas")
            ),
            "links": OutputSimulationEconomyMcIndScnLinks(
                config.next_file("links")
            ),
        }
        return children
