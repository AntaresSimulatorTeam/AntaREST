from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.input.hydro.allocation.area import (
    InputHydroAllocationArea,
)


class InputHydroAllocation(FolderNode):
    def build(self) -> TREE:
        children: TREE = {
            a: InputHydroAllocationArea(
                self.context, self.config.next_file(f"{a}.ini"), area=a
            )
            for a in self.config.area_names()
        }
        return children
