from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.input.hydro.allocation.area import (
    InputHydroAllocationArea,
)


class InputHydroAllocation(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            a: InputHydroAllocationArea(
                self.context, config.next_file(f"{a}.ini"), area=a
            )
            for a in config.area_names()
        }
        return children
