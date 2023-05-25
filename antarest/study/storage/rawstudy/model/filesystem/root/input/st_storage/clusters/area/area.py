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
from antarest.study.storage.rawstudy.model.filesystem.root.input.st_storage.clusters.area.list import (
    InputSTStorageAreaList,
)


class InputSTStorageArea(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        area: str,
    ):
        super().__init__(context, config)
        self.area = area

    def build(self) -> TREE:
        # Each area has a folder containing a file named "list.ini"
        # If the area does not have any short term storage cluster, the file is empty.
        children: TREE = {
            "list": InputSTStorageAreaList(
                self.context, self.config.next_file("list.ini"), self.area
            )
        }
        return children
