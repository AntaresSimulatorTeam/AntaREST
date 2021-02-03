from antarest.storage_api.filesystem.config.model import StudyConfig
from antarest.storage_api.filesystem.folder_node import FolderNode
from antarest.storage_api.filesystem.inode import TREE
from antarest.storage_api.filesystem.root.output.simulation.mode.mcall.areas.item.id import (
    OutputSimulationModeMcAllAreasItemId as Id,
)
from antarest.storage_api.filesystem.root.output.simulation.mode.mcall.areas.item.values import (
    OutputSimulationModeMcAllAreasItemValues as Values,
)


class OutputSimulationModeMcAllAreasSet(FolderNode):
    def __init__(self, config: StudyConfig, set: str):
        FolderNode.__init__(self, config)
        self.set = set

    def build(self, config: StudyConfig) -> TREE:
        children: TREE = dict()
        for timing in config.get_filters_synthesis(self.set):
            children[f"id-{timing}"] = Id(config.next_file(f"id-{timing}.txt"))

        for timing in config.get_filters_synthesis(self.set):
            children[f"values-{timing}"] = Values(
                config.next_file(f"values-{timing}.txt")
            )

        return children
