from api_iso_antares.filesystem.config.model import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.output.simulation.economy.mcall.links.item.item import (
    OutputSimulationEconomyMcAllLinksItem as Item,
)


class _OutputSimulationEconomyMcAllLinksBis(FolderNode):
    def __init__(self, config: Config, area: str):
        FolderNode.__init__(self, config)
        self.area = area

    def build(self, config: Config) -> TREE:
        children: TREE = {}
        for link in config.get_links(self.area):
            name = f"{self.area} - {link}"
            children[link] = Item(config.next_file(name), self.area, link)
        return children


class OutputSimulationEconomyMcAllLinks(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {}

        for area in config.area_names:
            children[area] = _OutputSimulationEconomyMcAllLinksBis(
                config, area
            )

        return children
