from antarest.storage_api.filesystem.config.model import StudyConfig
from antarest.storage_api.filesystem.folder_node import FolderNode
from antarest.storage_api.filesystem.inode import TREE
from antarest.storage_api.filesystem.root.input.hydro.common.capacity.capacity import (
    InputHydroCommonCapacity,
)


class InputHydroCommon(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            "capacity": InputHydroCommonCapacity(config.next_file("capacity"))
        }
        return children
