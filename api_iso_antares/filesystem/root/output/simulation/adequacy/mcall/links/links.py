from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.output.simulation.adequacy.mcall.links.item.item import (
    OutputSimulationAdequacyMcAllLinksItem as Item,
)


class _OutputSimulationAdequacyMcAllLinksBis(FolderNode):
    def __init__(self, config: Config, area: str):
        children: TREE = {}
        for link in config.get_links(area):
            name = f"{area} - {link}"
            children[link] = Item(config.next_file(name), area, link)
        FolderNode.__init__(self, config, children)


class OutputSimulationAdequacyMcAllLinks(FolderNode):
    def __init__(self, config: Config):
        children: TREE = {}

        for area in config.area_names:
            children[area] = _OutputSimulationAdequacyMcAllLinksBis(
                config, area
            )

        FolderNode.__init__(self, config, children)
