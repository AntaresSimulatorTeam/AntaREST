from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.json_file_node import (
    JsonFileNode,
)


class Xpansion(FolderNode):
    def build(self) -> TREE:
        return {
            "out": JsonFileNode(
                self.context, self.config.next_file("out.json")
            ),
            "last_iteration": JsonFileNode(
                self.context, self.config.next_file("last_iteration.json")
            ),
        }
