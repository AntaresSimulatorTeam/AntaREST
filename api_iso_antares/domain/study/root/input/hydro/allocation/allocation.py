from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.folder_node import FolderNode
from api_iso_antares.domain.study.inode import TREE
from api_iso_antares.domain.study.root.input.hydro.allocation.area import (
    InputHydroAllocationArea,
)


class InputHydroAllocation(FolderNode):
    def __init__(self, config: Config):
        children: TREE = {
            a: InputHydroAllocationArea(config.next_file(f"{a}.ini"), area=a)
            for a in config.area_names
        }
        FolderNode.__init__(self, children)
