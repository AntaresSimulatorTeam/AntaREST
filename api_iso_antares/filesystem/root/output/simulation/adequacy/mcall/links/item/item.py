from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.output.simulation.adequacy.mcall.links.item.values import (
    OutputSimulationAdequacyMcAllLinksItemValues as Values,
)


class OutputSimulationAdequacyMcAllLinksItem(FolderNode):
    def __init__(self, config: Config, area: str, link: str):
        children: TREE = {
            f"values-{timing}": Values(
                config.next_file(f"values-{timing}.txt")
            )
            for timing in config.get_filters_synthesis(area, link)
        }
        FolderNode.__init__(self, config, children)
