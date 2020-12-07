from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.folder_node import FolderNode
from api_iso_antares.domain.study.inode import TREE
from api_iso_antares.domain.study.root.input.hydro.allocation.allocation import (
    InputHydroAllocation,
)
from api_iso_antares.domain.study.root.input.hydro.common.common import (
    InputHydroCommon,
)
from api_iso_antares.domain.study.root.input.hydro.hydro_ini import (
    InputHydroIni,
)
from api_iso_antares.domain.study.root.input.hydro.prepro.prepro import (
    InputHydroPrepro,
)
from api_iso_antares.domain.study.root.input.hydro.series.series import (
    InputHydroSeries,
)


class InputHydro(FolderNode):
    def __init__(self, config: Config):
        children: TREE = {
            "allocation": InputHydroAllocation(config.next_file("allocation")),
            "common": InputHydroCommon(config.next_file("common")),
            "prepro": InputHydroPrepro(config.next_file("prepro")),
            "series": InputHydroSeries(config.next_file("series")),
            "hydro": InputHydroIni(config.next_file("hydro.ini")),
        }
        FolderNode.__init__(self, children)
