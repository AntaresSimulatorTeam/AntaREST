from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.input.hydro.common.capacity.capacity import (
    InputHydroCommonCapacity,
)


class InputHydroCommon(FolderNode):
    def build(self) -> TREE:
        children: TREE = {
            "capacity": InputHydroCommonCapacity(
                self.context, self.config.next_file("capacity")
            )
        }
        return children
