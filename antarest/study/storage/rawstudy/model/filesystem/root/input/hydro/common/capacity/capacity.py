from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.input.hydro.common.capacity.item import (
    InputHydroCommonCapacityItem,
)


class InputHydroCommonCapacity(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
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
