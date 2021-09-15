from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.input.hydro.allocation.allocation import (
    InputHydroAllocation,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.hydro.common.common import (
    InputHydroCommon,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.hydro.hydro_ini import (
    InputHydroIni,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.hydro.prepro.prepro import (
    InputHydroPrepro,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.hydro.series.series import (
    InputHydroSeries,
)


class InputHydro(FolderNode):
    def build(self) -> TREE:
        children: TREE = {
            "allocation": InputHydroAllocation(
                self.context, self.config.next_file("allocation")
            ),
            "common": InputHydroCommon(
                self.context, self.config.next_file("common")
            ),
            "prepro": InputHydroPrepro(
                self.context, self.config.next_file("prepro")
            ),
            "series": InputHydroSeries(
                self.context, self.config.next_file("series")
            ),
            "hydro": InputHydroIni(
                self.context, self.config.next_file("hydro.ini")
            ),
        }
        return children
