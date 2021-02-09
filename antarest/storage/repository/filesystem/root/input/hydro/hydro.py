from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.input.hydro.allocation.allocation import (
    InputHydroAllocation,
)
from antarest.storage.repository.filesystem.root.input.hydro.common.common import (
    InputHydroCommon,
)
from antarest.storage.repository.filesystem.root.input.hydro.hydro_ini import (
    InputHydroIni,
)
from antarest.storage.repository.filesystem.root.input.hydro.prepro.prepro import (
    InputHydroPrepro,
)
from antarest.storage.repository.filesystem.root.input.hydro.series.series import (
    InputHydroSeries,
)


class InputHydro(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            "allocation": InputHydroAllocation(config.next_file("allocation")),
            "common": InputHydroCommon(config.next_file("common")),
            "prepro": InputHydroPrepro(config.next_file("prepro")),
            "series": InputHydroSeries(config.next_file("series")),
            "hydro": InputHydroIni(config.next_file("hydro.ini")),
        }
        return children
