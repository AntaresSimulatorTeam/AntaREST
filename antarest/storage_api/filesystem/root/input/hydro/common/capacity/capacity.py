from antarest.storage_api.filesystem.config.model import Config
from antarest.storage_api.filesystem.folder_node import FolderNode
from antarest.storage_api.filesystem.inode import TREE
from antarest.storage_api.filesystem.root.input.hydro.common.capacity.item import (
    InputHydroCommonCapacityItem,
)


class InputHydroCommonCapacity(FolderNode):
    def build(self, config: Config) -> TREE:
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
                    config.next_file(f"{name}.txt")
                )
        return children
