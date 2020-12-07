from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.folder_node import FolderNode
from api_iso_antares.domain.study.root.input.hydro.allocation.allocation import (
    InputHydroAllocation,
)
from api_iso_antares.domain.study.root.input.hydro.common.common import (
    InputHydroCommon,
)


class InputHydro(FolderNode):
    def __init__(self, config: Config):
        children = {
            "allocation": InputHydroAllocation(config.next_file("allocation")),
            "common": InputHydroCommon(config.next_file("common")),
        }
        FolderNode.__init__(self, children)
