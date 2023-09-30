from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.input.st_storage.clusters.clusters import (
    InputSTStorageClusters,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.st_storage.series.series import InputSTStorageSeries


class InputSTStorage(FolderNode):
    # Short-term storage objects are introduced in the v8.6 of AntaresSimulator.
    # This new object simplifies the previously complex modeling of short-term storage such as batteries or STEPs.
    def build(self) -> TREE:
        children: TREE = {
            "clusters": InputSTStorageClusters(self.context, self.config.next_file("clusters")),
            "series": InputSTStorageSeries(self.context, self.config.next_file("series")),
        }
        return children
