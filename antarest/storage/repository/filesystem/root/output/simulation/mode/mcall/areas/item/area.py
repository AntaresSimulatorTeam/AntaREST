from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.output.simulation.mode.mcall.areas.item.details import (
    OutputSimulationModeMcAllAreasItemDetails as Details,
)
from antarest.storage.repository.filesystem.root.output.simulation.mode.mcall.areas.item.id import (
    OutputSimulationModeMcAllAreasItemId as Id,
)
from antarest.storage.repository.filesystem.root.output.simulation.mode.mcall.areas.item.values import (
    OutputSimulationModeMcAllAreasItemValues as Values,
)


class OutputSimulationModeMcAllAreasArea(FolderNode):
    def __init__(self, config: StudyConfig, area: str):
        FolderNode.__init__(self, config)
        self.area = area

    def build(self, config: StudyConfig) -> TREE:
        children: TREE = dict()

        filters = config.get_filters_synthesis(self.area)

        for timing in (
            filters
            if config.get_thermal_names(self.area, only_enabled=True)
            else []
        ):
            children[f"details-{timing}"] = Details(
                config.next_file(f"details-{timing}.txt"), timing, self.area
            )

        for timing in filters:
            children[f"id-{timing}"] = Id(
                config.next_file(f"id-{timing}.txt"), timing, self.area
            )

            children[f"values-{timing}"] = Values(
                config.next_file(f"values-{timing}.txt"), timing, self.area
            )

        return children
