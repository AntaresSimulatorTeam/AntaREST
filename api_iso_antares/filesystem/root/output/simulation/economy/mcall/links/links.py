from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.output.simulation.economy.mcall.links.item.item import (
    OutputSimulationEconomyMcAllLinksItem as Item,
)


class _OutputSimulationEconomyMcAllLinksBis(FolderNode):
    def __init__(self, config: Config, area: str):
        children: TREE = {}
        for link in config.get_links(area):
            name = f"{area} - {link}"
            children[link] = Item(config.next_file(name), area, link)
        FolderNode.__init__(self, children)


class OutputSimulationEconomyMcAllLinks(FolderNode):
    def __init__(self, config: Config):
        children: TREE = {}

        for area in config.area_names:
            children[area] = _OutputSimulationEconomyMcAllLinksBis(
                config, area
            )

        FolderNode.__init__(self, children)
