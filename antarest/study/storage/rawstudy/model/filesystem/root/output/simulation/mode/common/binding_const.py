from typing import cast

from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.output_series_matrix import (
    LinkOutputSeriesMatrix,
    BindingConstraintOutputSeriesMatrix,
)


class OutputSimulationBindingConstraintItem(FolderNode):
    def build(self) -> TREE:
        children: TREE = {}

        # filters = self.config.get_filters_synthesis(self.area, self.link)
        # todo get the config related to this output (now this may fail if input has changed since the launch)
        filters = ["hourly", "daily", "weekly", "monthly", "annual"]

        for timing in filters:
            children[f"values-{timing}"] = BindingConstraintOutputSeriesMatrix(
                self.context,
                self.config.next_file(f"values-{timing}.txt"),
                timing,
            )

        return {
            child: children[child]
            for child in children
            if cast(LinkOutputSeriesMatrix, children[child]).file_exists()
        }
