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
from antarest.study.storage.rawstudy.model.filesystem.root.input.st_storage.series.area.st_storage.st_storage import (
    InputSTStorageAreaStorage,
)


class InputSTStorageSeriesArea(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        area: str,
    ):
        super().__init__(context, config)
        self.area = area

    def build(self) -> TREE:
        children: TREE = {
            st_storage_id: InputSTStorageAreaStorage(
                self.context, self.config.next_file(st_storage_id)
            )
            for st_storage_id in self.config.get_st_storage_ids(self.area)
        }
        return children
