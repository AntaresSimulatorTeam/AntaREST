from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.output.simulation.mode.mcind.scn.areas.item.details import (
    OutputSimulationModeMcIndScnAreasItemDetails as Details,
)

from antarest.storage.repository.filesystem.root.output.simulation.mode.mcind.scn.areas.item.values import (
    OutputSimulationModeMcIndScnAreasItemValues as Values,
)


class OutputSimulationModeMcIndScnAreasArea(FolderNode):
    def __init__(self, config: StudyConfig, area: str):
        FolderNode.__init__(self, config)
        self.area = area

    def build(self, config: StudyConfig) -> TREE:
        children: TREE = dict()

        for timing in config.get_filters_year(self.area):
            detail_config = config.next_file(f"details-{timing}.txt")
            if detail_config.path.exists():
                children[f"details-{timing}"] = Details(detail_config)

        for timing in config.get_filters_year(self.area):
            children[f"values-{timing}"] = Values(
                config.next_file(f"values-{timing}.txt")
            )

        return children
