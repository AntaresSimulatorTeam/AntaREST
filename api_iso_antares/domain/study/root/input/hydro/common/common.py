from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.folder_node import FolderNode
from api_iso_antares.domain.study.root.input.hydro.common.capacity.capacity import (
    InputHydroCommonCapacity,
)


class InputHydroCommon(FolderNode):
    def __init__(self, config: Config):
        children = {
            "capacity": InputHydroCommonCapacity(config.next_file("capacity"))
        }
        FolderNode.__init__(self, children)
