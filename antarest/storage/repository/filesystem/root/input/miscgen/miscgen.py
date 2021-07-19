from antarest.storage.repository.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.input.miscgen.area import (
    InputMiscGenArea,
)


class InputMiscGen(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            f"miscgen-{a}": InputMiscGenArea(
                self.context, config.next_file(f"miscgen-{a}.txt")
            )
            for a in config.area_names()
        }
        return children
