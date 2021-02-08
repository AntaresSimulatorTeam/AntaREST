from antarest.storage.filesystem.config.model import StudyConfig
from antarest.storage.filesystem.folder_node import FolderNode
from antarest.storage.filesystem.inode import TREE
from antarest.storage.filesystem.root.output.simulation.mode.mcind.scn.areas.item.details import (
    OutputSimulationModeMcIndScnAreasItemDetails as Details,
)

from antarest.storage.filesystem.root.output.simulation.mode.mcind.scn.areas.item.values import (
    OutputSimulationModeMcIndScnAreasItemValues as Values,
)


class OutputSimulationModeMcIndScnAreasArea(FolderNode):
    def __init__(self, config: StudyConfig, area: str):
        FolderNode.__init__(self, config)
        self.area = area

    def build(self, config: StudyConfig) -> TREE:
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
