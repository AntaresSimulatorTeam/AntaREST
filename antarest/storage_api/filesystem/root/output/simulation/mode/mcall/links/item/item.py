from antarest.storage_api.filesystem.config.model import StudyConfig
from antarest.storage_api.filesystem.folder_node import FolderNode
from antarest.storage_api.filesystem.inode import TREE
from antarest.storage_api.filesystem.root.output.simulation.mode.mcall.links.item.values import (
    OutputSimulationModeMcAllLinksItemValues as Values,
)
from antarest.storage_api.filesystem.root.output.simulation.mode.mcall.links.item.id import (
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
                config.next_file(f"values-{timing}.txt")
            )
            children[f"id-{timing}"] = Id(config.next_file(f"id-{timing}.txt"))
        return children
