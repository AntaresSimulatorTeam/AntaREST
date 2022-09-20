from typing import List

from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.ini_file_node import (
    IniFileNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE


class SensitivityConfig(FolderNode):
    def build(self) -> TREE:
        types = {"epsilon": float, "capex": bool, "projection": List[str]}
        return {
            "sensitivity_in": IniFileNode(
                self.context,
                self.config.next_file("sensitivity_in.json"),
                types,
            )
        }
