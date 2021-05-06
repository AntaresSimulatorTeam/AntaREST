from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.output.simulation.mode.mcall.links.item.values import (
    OutputSimulationModeMcAllLinksItemValues as Values,
)
from antarest.storage.repository.filesystem.root.output.simulation.mode.mcall.links.item.id import (
    OutputSimulationModeMcAllLinksItemId as Id,
)


class OutputSimulationModeMcAllLinksItem(FolderNode):
    def __init__(self, config: StudyConfig, area: str, link: str):
        FolderNode.__init__(self, config)
        self.area = area
        self.link = link

    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {}
        for timing in config.get_filters_synthesis(self.area, self.link):
            children[f"values-{timing}"] = Values(
                config.next_file(f"values-{timing}.txt"), timing
            )
            children[f"id-{timing}"] = Id(
                config.next_file(f"id-{timing}.txt"), timing
            )
        return children
