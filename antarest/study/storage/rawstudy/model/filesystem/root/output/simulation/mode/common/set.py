from typing import cast

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


class OutputSimulationSet(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        set: str,
        mc_all: bool = True,
    ):
        FolderNode.__init__(self, context, config)
        self.set = set
        self.mc_all = mc_all

    def build(self) -> TREE:
        children: TREE = dict()

        # filters = self.config.get_filters_synthesis(self.set)
        # todo get the config related to this output (now this may fail if input has changed since the launch)
        filters = ["hourly", "daily", "weekly", "monthly", "annual"]

        for timing in filters:
            if self.mc_all:
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

        return {
            child: children[child]
            for child in children
            if cast(AreaOutputSeriesMatrix, children[child]).file_exists()
        }
