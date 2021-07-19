from antarest.storage.repository.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.repository.filesystem.context import ContextServer
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.output.simulation.mode.mcall.links.item.id import (
    OutputSimulationModeMcAllLinksItemId as Id,
)
from antarest.storage.repository.filesystem.root.output.simulation.mode.mcall.links.item.values import (
    OutputSimulationModeMcAllLinksItemValues as Values,
)


class OutputSimulationModeMcAllLinksItem(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        area: str,
        link: str,
    ):
        FolderNode.__init__(self, context, config)
        self.area = area
        self.link = link

    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {}
        for timing in config.get_filters_synthesis(self.area, self.link):
            children[f"values-{timing}"] = Values(
                self.context,
                config.next_file(f"values-{timing}.txt"),
                timing,
                self.area,
                self.link,
            )
            children[f"id-{timing}"] = Id(
                self.context,
                config.next_file(f"id-{timing}.txt"),
                timing,
                self.area,
                self.link,
            )
        return children
