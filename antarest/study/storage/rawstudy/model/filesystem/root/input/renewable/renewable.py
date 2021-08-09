from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.input.renewable.clusters import (
    ClusteredRenewableAreaCluster,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.renewable.series import (
    ClusteredRenewableAreaSeries,
)


class ClusteredRenewable(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            "clusters": ClusteredRenewableAreaCluster(
                self.context, config.next_file("clusters")
            ),
            "series": ClusteredRenewableAreaSeries(
                self.context, config.next_file("series")
            ),
        }

        return children
