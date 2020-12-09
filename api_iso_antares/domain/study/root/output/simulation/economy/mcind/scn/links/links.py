from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.folder_node import FolderNode
from api_iso_antares.domain.study.inode import TREE
from api_iso_antares.domain.study.root.output.simulation.economy.mcind.scn.links.item.item import (
    OutputSimulationEconomyMcIndScnLinksItem as Item,
)


class _OutputSimulationEconomyMcIndScnLinksBis(FolderNode):
    def __init__(self, config: Config, area: str):
        children: TREE = {}
        for link in config.get_links(area):
            name = f"{area} - {link}"
            children[link] = Item(config.next_file(name), area, link)
        FolderNode.__init__(self, children)


class OutputSimulationEconomyMcIndScnLinks(FolderNode):
    def __init__(self, config: Config):
        children: TREE = {}

        for area in config.area_names:
            children[area] = _OutputSimulationEconomyMcIndScnLinksBis(
                config, area
            )

        FolderNode.__init__(self, children)
