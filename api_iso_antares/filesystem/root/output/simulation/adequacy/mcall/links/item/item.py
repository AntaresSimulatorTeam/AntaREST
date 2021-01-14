from api_iso_antares.filesystem.config.model import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.output.simulation.adequacy.mcall.links.item.values import (
    OutputSimulationAdequacyMcAllLinksItemValues as Values,
)
from api_iso_antares.filesystem.root.output.simulation.adequacy.mcall.links.item.id import (
    OutputSimulationAdequacyMcAllLinksItemId as Id,
)


class OutputSimulationAdequacyMcAllLinksItem(FolderNode):
    def __init__(self, config: Config, area: str, link: str):
        FolderNode.__init__(self, config)
        self.area = area
        self.link = link

    def build(self, config: Config) -> TREE:
        children: TREE = {}
        for timing in config.get_filters_synthesis(self.area, self.link):
            children[f"values-{timing}"] = Values(
                config.next_file(f"values-{timing}.txt")
            )
            children[f"id-{timing}"] = Id(config.next_file(f"id-{timing}.txt"))
        return children
