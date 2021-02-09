from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.output.simulation.mode.mcind.scn.links.item.item import (
    OutputSimulationModeMcIndScnLinksItem as Item,
)


class _OutputSimulationModeMcIndScnLinksBis(FolderNode):
    def __init__(self, config: StudyConfig, area: str):
        FolderNode.__init__(self, config)
        self.area = area

    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {}
        for link in config.get_links(self.area):
            name = f"{self.area} - {link}"
            children[link] = Item(config.next_file(name), self.area, link)
        return children


class OutputSimulationModeMcIndScnLinks(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {}

        for area in config.area_names():
            children[area] = _OutputSimulationModeMcIndScnLinksBis(
                config, area
            )

        return children
