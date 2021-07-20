from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcall.areas.item.id import (
    OutputSimulationModeMcAllAreasItemId as Id,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcall.areas.item.values import (
    OutputSimulationModeMcAllAreasItemValues as Values,
)


class OutputSimulationModeMcAllAreasSet(FolderNode):
    def __init__(
        self, context: ContextServer, config: FileStudyTreeConfig, set: str
    ):
        FolderNode.__init__(self, context, config)
        self.set = set

    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = dict()
        for timing in config.get_filters_synthesis(self.set):
            children[f"id-{timing}"] = Id(
                self.context,
                config.next_file(f"id-{timing}.txt"),
                timing,
                self.set,
            )

            children[f"values-{timing}"] = Values(
                self.context,
                config.next_file(f"values-{timing}.txt"),
                timing,
                self.set,
            )

        return children
