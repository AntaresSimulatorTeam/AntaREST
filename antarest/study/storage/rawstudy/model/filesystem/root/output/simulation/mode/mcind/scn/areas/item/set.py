from antarest.storage.business.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.business.rawstudy.model.filesystem.context import ContextServer
from antarest.storage.business.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.storage.business.rawstudy.model.filesystem.inode import TREE
from antarest.storage.business.rawstudy.model.filesystem.root.output.simulation.mode.mcind.scn.areas.item.values import (
    OutputSimulationModeMcIndScnAreasItemValues as Values,
)


class OutputSimulationModeMcIndScnAreasSet(FolderNode):
    def __init__(
        self, context: ContextServer, config: FileStudyTreeConfig, set: str
    ):
        FolderNode.__init__(self, context, config)
        self.set = set

    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = dict()

        for timing in config.get_filters_year(self.set):
            children[f"values-{timing}"] = Values(
                self.context,
                config.next_file(f"values-{timing}.txt"),
                timing,
                self.set,
            )

        return children
