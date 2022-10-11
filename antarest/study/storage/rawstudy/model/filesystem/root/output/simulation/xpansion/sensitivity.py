from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.json_file_node import (
    JsonFileNode,
)
from antarest.study.storage.rawstudy.model.filesystem.raw_file_node import (
    RawFileNode,
)


class Sensitivity(FolderNode):
    def build(self) -> TREE:
        return {
            "out": JsonFileNode(
                self.context, self.config.next_file("sensitivity_out.json")
            ),
            "log": RawFileNode(
                self.context, self.config.next_file("sensitivity_log.txt")
            ),
        }
