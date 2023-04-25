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
    InputShortTermStorageAreaStorage,
)


class InputShortTermStorageSeriesArea(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        area: str,
    ):
        FolderNode.__init__(self, context, config)
        self.area = area

    def build(self) -> TREE:
        children: TREE = {
            st_storage: InputShortTermStorageAreaStorage(
                self.context, self.config.next_file(st_storage)
            )
            for st_storage in self.config.get_short_term_storage_names(
                self.area
            )
        }
        return children
