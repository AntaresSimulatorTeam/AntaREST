from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.output.simulation.adequacy.mcind.scn.areas.item.details import (
    OutputSimulationAdequacyMcIndScnAreasItemDetails as Details,
)

from api_iso_antares.filesystem.root.output.simulation.adequacy.mcind.scn.areas.item.values import (
    OutputSimulationAdequacyMcIndScnAreasItemValues as Values,
)


class OutputSimulationAdequacyMcIndScnAreasItem(FolderNode):
    def __init__(self, config: Config, area: str):
        FolderNode.__init__(self, config)
        self.area = area

    def build(self, config: Config) -> TREE:
        children: TREE = dict()

        for timing in config.get_filters_year(self.area):
            children[f"details-{timing}"] = Details(
                config.next_file(f"details-{timing}.txt")
            )

        for timing in config.get_filters_year(self.area):
            children[f"values-{timing}"] = Values(
                config.next_file(f"values-{timing}.txt")
            )

        return children
