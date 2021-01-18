from api_iso_antares.filesystem.config.model import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.output.simulation.mode.mcall.links.item.item import (
    OutputSimulationModeMcAllLinksItem as Item,
)


class _OutputSimulationModeMcAllLinksBis(FolderNode):
    def __init__(self, config: Config, area: str):
        FolderNode.__init__(self, config)
        self.area = area

    def build(self, config: Config) -> TREE:
        children: TREE = {}
        for link in config.get_links(self.area):
            name = f"{self.area} - {link}"
            children[link] = Item(config.next_file(name), self.area, link)
        return children


class OutputSimulationModeMcAllLinks(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {}

        for area in config.area_names():
            children[area] = _OutputSimulationModeMcAllLinksBis(config, area)

        return children
