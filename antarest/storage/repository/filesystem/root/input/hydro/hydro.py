from antarest.storage.repository.filesystem.config.model import (
    FileStudyTreeConfig,
)
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
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            "allocation": InputHydroAllocation(
                self.context, config.next_file("allocation")
            ),
            "common": InputHydroCommon(
                self.context, config.next_file("common")
            ),
            "prepro": InputHydroPrepro(
                self.context, config.next_file("prepro")
            ),
            "series": InputHydroSeries(
                self.context, config.next_file("series")
            ),
            "hydro": InputHydroIni(
                self.context, config.next_file("hydro.ini")
            ),
        }
        return children
