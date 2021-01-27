from AntaREST.storage_api.filesystem.config.model import Config
from AntaREST.storage_api.filesystem.folder_node import FolderNode
from AntaREST.storage_api.filesystem.inode import TREE
from AntaREST.storage_api.filesystem.root.input.hydro.common.capacity.capacity import (
    InputHydroCommonCapacity,
)


class InputHydroCommon(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            "capacity": InputHydroCommonCapacity(config.next_file("capacity"))
        }
        return children
