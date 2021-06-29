from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.context import ContextServer
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
    def __init__(self, context: ContextServer, config: StudyConfig, area: str):
        FolderNode.__init__(self, context, config)
        self.area = area

    def build(self, config: StudyConfig) -> TREE:
        children: TREE = dict()

        filters = config.get_filters_synthesis(self.area)

        for freq in (
            filters
            if config.get_thermal_names(self.area, only_enabled=True)
            else []
        ):
            children[f"details-{freq}"] = Details(
                self.context,
                config.next_file(f"details-{freq}.txt"),
                freq,
                self.area,
            )

        for freq in filters:
            children[f"id-{freq}"] = Id(
                self.context,
                config.next_file(f"id-{freq}.txt"),
                freq,
                self.area,
            )

            children[f"values-{freq}"] = Values(
                self.context,
                config.next_file(f"values-{freq}.txt"),
                freq,
                self.area,
            )

        return children
