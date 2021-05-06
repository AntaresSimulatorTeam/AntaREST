from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.output.simulation.mode.mcind.scn.areas.item.values import (
    OutputSimulationModeMcIndScnAreasItemValues as Values,
)


class OutputSimulationModeMcIndScnAreasSet(FolderNode):
    def __init__(self, config: StudyConfig, set: str):
        FolderNode.__init__(self, config)
        self.set = set

    def build(self, config: StudyConfig) -> TREE:
        children: TREE = dict()

        for timing in config.get_filters_year(self.set):
            children[f"values-{timing}"] = Values(
                config.next_file(f"values-{timing}.txt"), timing
            )

        return children
