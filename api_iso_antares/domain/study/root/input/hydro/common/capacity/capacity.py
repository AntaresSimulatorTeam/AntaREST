from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.folder_node import FolderNode
from api_iso_antares.domain.study.inode import TREE
from api_iso_antares.domain.study.root.input.hydro.common.capacity.item import (
    InputHydroCommonCapacityItem,
)


class InputHydroCommonCapacity(FolderNode):
    def __init__(self, config: Config):
        children: TREE = dict()
        for area in config.area_names:
            for file in [
                "creditmodulation",
                "inflowPattern",
                "maxpower",
                "reservoir",
                "waterValues",
            ]:
                name = f"{file}_{area}"
                children[name] = InputHydroCommonCapacityItem(
                    config.next_file(f"{name}.txt")
                )
        FolderNode.__init__(self, children)
