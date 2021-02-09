from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.input.miscgen.area import (
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
