from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.input.st_storage.series.area.area import (
    InputSTStorageSeriesArea,
)


class InputSTStorageSeries(FolderNode):
    # For each short-term storage, a time-series matrix is created after the name of the cluster.
    # This matrix is created inside the folder's area corresponding to the cluster.
    def build(self) -> TREE:
        children: TREE = {
            a: InputSTStorageSeriesArea(
                self.context, self.config.next_file(a), area=a
            )
            for a in self.config.area_names()
        }
        return children
