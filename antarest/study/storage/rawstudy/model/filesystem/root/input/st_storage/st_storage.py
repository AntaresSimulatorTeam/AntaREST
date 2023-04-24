from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.input.st_storage.clusters.clusters import (
    InputShortTermStorageClusters,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.st_storage.series.series import (
    InputShortTermStorageSeries,
)


class InputShortTermStorage(FolderNode):
    def build(self) -> TREE:
        children: TREE = {
            "clusters": InputShortTermStorageClusters(
                self.context, self.config.next_file("clusters")
            ),
            "series": InputShortTermStorageSeries(
                self.context, self.config.next_file("series")
            ),
        }
        return children
