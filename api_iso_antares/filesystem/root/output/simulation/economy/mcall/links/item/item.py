from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.output.simulation.economy.mcind.scn.links.item.values import (
    OutputSimulationEconomyMcIndScnLinksItemValues as Values,
)


class OutputSimulationEconomyMcAllLinksItem(FolderNode):
    def __init__(self, config: Config, area: str, link: str):
        FolderNode.__init__(self, config)
        self.area = area
        self.link = link

    def build(self, config: Config) -> TREE:
        children: TREE = {
            f"values-{timing}": Values(
                config.next_file(f"values-{timing}.txt")
            )
            for timing in config.get_filters_synthesis(self.area, self.link)
        }
        return children
