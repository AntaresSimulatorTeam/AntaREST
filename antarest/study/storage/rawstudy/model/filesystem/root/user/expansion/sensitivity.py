from typing import List

from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.json_file_node import (
    JsonFileNode,
)


class SensitivityConfig(FolderNode):
    def build(self) -> TREE:
        types = {"epsilon": float, "capex": bool, "projection": List[str]}
        return {
            "sensitivity_in": JsonFileNode(
                self.context,
                self.config.next_file("sensitivity_in.json"),
                types,
            )
        }
