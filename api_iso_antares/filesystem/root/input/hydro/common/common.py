from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.input.hydro.common.capacity.capacity import (
    InputHydroCommonCapacity,
)


class InputHydroCommon(FolderNode):
    def __init__(self, config: Config):
        children: TREE = {
            "capacity": InputHydroCommonCapacity(config.next_file("capacity"))
        }
        FolderNode.__init__(self, children)
