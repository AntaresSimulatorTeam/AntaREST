from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.output.simulation.economy.mcind.scn.areas.item.details import (
    OutputSimulationEconomyMcIndScnAreasItemDetails as Details,
)

from api_iso_antares.filesystem.root.output.simulation.economy.mcind.scn.areas.item.values import (
    OutputSimulationEconomyMcIndScnAreasItemValues as Values,
)


class OutputSimulationEconomyMcIndScnAreasItem(FolderNode):
    def __init__(self, config: Config, area: str):
        children: TREE = dict()

        for timing in config.get_filters_year(area):
            children[f"details-{timing}"] = Details(
                config.next_file(f"details-{timing}.txt")
            )

        for timing in config.get_filters_year(area):
            children[f"values-{timing}"] = Values(
                config.next_file(f"values-{timing}.txt")
            )

        FolderNode.__init__(self, children)
