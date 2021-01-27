from AntaREST.storage_api.filesystem.config.model import Config
from AntaREST.storage_api.filesystem.folder_node import FolderNode
from AntaREST.storage_api.filesystem.inode import TREE
from AntaREST.storage_api.filesystem.root.output.simulation.mode.mcind.scn.links.item.values import (
    OutputSimulationModeMcIndScnLinksItemValues as Values,
)


class OutputSimulationModeMcIndScnLinksItem(FolderNode):
    def __init__(self, config: Config, area: str, link: str):
        FolderNode.__init__(self, config)
        self.area = area
        self.link = link

    def build(self, config: Config) -> TREE:
        children: TREE = {
            f"values-{timing}": Values(
                config.next_file(f"values-{timing}.txt")
            )
            for timing in config.get_filters_year(self.area, self.link)
        }
        return children
