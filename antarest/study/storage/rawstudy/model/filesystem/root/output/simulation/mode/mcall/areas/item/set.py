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
from antarest.study.storage.rawstudy.model.filesystem.matrix.output_series_matrix import (
    AreaOutputSeriesMatrix,
)


class OutputSimulationModeMcAllAreasSet(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        set: str,
    ):
        FolderNode.__init__(self, context, config)
        self.set = set

    def build(self) -> TREE:
        children: TREE = dict()
        for timing in self.config.get_filters_synthesis(self.set):
            children[f"id-{timing}"] = AreaOutputSeriesMatrix(
                self.context,
                self.config.next_file(f"id-{timing}.txt"),
                timing,
                self.set,
            )

            children[f"values-{timing}"] = AreaOutputSeriesMatrix(
                self.context,
                self.config.next_file(f"values-{timing}.txt"),
                timing,
                self.set,
            )

        return children
