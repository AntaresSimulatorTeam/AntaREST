from storage_api.filesystem.config.model import Config
from storage_api.filesystem.folder_node import FolderNode
from storage_api.filesystem.inode import TREE
from storage_api.filesystem.root.input.miscgen.area import (
    InputMiscGenArea,
)


class InputMiscGen(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            f"miscgen-{a}": InputMiscGenArea(
                config.next_file(f"miscgen-{a}.txt")
            )
            for a in config.area_names()
        }
        return children
