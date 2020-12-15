from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.input.hydro.allocation.area import (
    InputHydroAllocationArea,
)


class InputHydroAllocation(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            a: InputHydroAllocationArea(config.next_file(f"{a}.ini"), area=a)
            for a in config.area_names
        }
        return children
