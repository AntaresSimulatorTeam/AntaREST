from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.input.hydro.common.capacity.item import (
    InputHydroCommonCapacityItem,
)


class InputHydroCommonCapacity(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = dict()
        for area in config.area_names():
            for file in [
                "creditmodulations",
                "inflowPattern",
                "maxpower",
                "reservoir",
                "waterValues",
            ]:
                name = f"{file}_{area}"
                children[name] = InputHydroCommonCapacityItem(
                    self.context, config.next_file(f"{name}.txt")
                )
        return children
