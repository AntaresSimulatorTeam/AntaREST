from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.folder_node import FolderNode
from api_iso_antares.domain.study.inode import TREE
from api_iso_antares.domain.study.root.output.simulation.economy.mcind.scn.links.item.values import (
    OutputSimulationEconomyMcIndScnLinksItemValues as Values,
)


class OutputSimulationEconomyMcIndScnLinksItem(FolderNode):
    def __init__(self, config: Config, area: str, link: str):
        children: TREE = {
            f"values-{timing}": Values(
                config.next_file(f"values-{timing}.txt")
            )
            for timing in config.get_filters_year(area, link)
        }
        FolderNode.__init__(self, children)
