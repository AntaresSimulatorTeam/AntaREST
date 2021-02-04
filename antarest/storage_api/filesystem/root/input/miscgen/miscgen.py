from antarest.storage_api.filesystem.config.model import StudyConfig
from antarest.storage_api.filesystem.folder_node import FolderNode
from antarest.storage_api.filesystem.inode import TREE
from antarest.storage_api.filesystem.root.input.miscgen.area import (
    InputMiscGenArea,
)


class InputMiscGen(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            f"miscgen-{a}": InputMiscGenArea(
                config.next_file(f"miscgen-{a}.txt")
            )
            for a in config.area_names()
        }
        return children
