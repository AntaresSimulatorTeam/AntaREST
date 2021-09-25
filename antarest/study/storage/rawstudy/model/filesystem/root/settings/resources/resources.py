from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.raw_file_node import (
    RawFileNode,
)


class Resources(FolderNode):
    def build(self) -> TREE:
        children: TREE = {
            "study": RawFileNode(
                self.context, self.config.next_file("study.ico")
            )
        }
        return children
