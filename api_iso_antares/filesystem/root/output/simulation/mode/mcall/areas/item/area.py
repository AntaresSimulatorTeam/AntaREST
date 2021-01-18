from api_iso_antares.filesystem.config.model import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.output.simulation.mode.mcall.areas.item.details import (
    OutputSimulationModeMcAllAreasItemDetails as Details,
)
from api_iso_antares.filesystem.root.output.simulation.mode.mcall.areas.item.id import (
    OutputSimulationModeMcAllAreasItemId as Id,
)
from api_iso_antares.filesystem.root.output.simulation.mode.mcall.areas.item.values import (
    OutputSimulationModeMcAllAreasItemValues as Values,
)


class OutputSimulationModeMcAllAreasArea(FolderNode):
    def __init__(self, config: Config, area: str):
        FolderNode.__init__(self, config)
        self.area = area

    def build(self, config: Config) -> TREE:
        children: TREE = dict()

        filters = config.get_filters_synthesis(self.area)

        for timing in filters if config.get_thermals(self.area) else []:
            children[f"details-{timing}"] = Details(
                config.next_file(f"details-{timing}.txt")
            )

        for timing in filters:
            children[f"id-{timing}"] = Id(config.next_file(f"id-{timing}.txt"))

        for timing in filters:
            children[f"values-{timing}"] = Values(
                config.next_file(f"values-{timing}.txt")
            )

        return children
