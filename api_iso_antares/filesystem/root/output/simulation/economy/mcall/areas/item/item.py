from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.output.simulation.economy.mcall.areas.item.details import (
    OutputSimulationEconomyMcAllAreasItemDetails as Details,
)
from api_iso_antares.filesystem.root.output.simulation.economy.mcall.areas.item.id import (
    OutputSimulationEconomyMcAllAreasItemId as Id,
)
from api_iso_antares.filesystem.root.output.simulation.economy.mcall.areas.item.values import (
    OutputSimulationEconomyMcAllAreasItemValues as Values,
)


class OutputSimulationEconomyMcAllAreasItem(FolderNode):
    def __init__(self, config: Config, area: str):
        children: TREE = dict()

        for timing in config.get_filters_synthesis(area):
            children[f"details-{timing}"] = Details(
                config.next_file(f"details-{timing}.txt")
            )

        for timing in config.get_filters_synthesis(area):
            children[f"id-{timing}"] = Id(config.next_file(f"id-{timing}.txt"))

        for timing in config.get_filters_synthesis(area):
            children[f"values-{timing}"] = Values(
                config.next_file(f"values-{timing}.txt")
            )

        FolderNode.__init__(self, config, children)
