from storage_api.filesystem.config.model import Config
from storage_api.filesystem.folder_node import FolderNode
from storage_api.filesystem.inode import TREE
from storage_api.filesystem.root.input.hydro.allocation.area import (
    InputHydroAllocationArea,
)


class InputHydroAllocation(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            a: InputHydroAllocationArea(config.next_file(f"{a}.ini"), area=a)
            for a in config.area_names()
        }
        return children
