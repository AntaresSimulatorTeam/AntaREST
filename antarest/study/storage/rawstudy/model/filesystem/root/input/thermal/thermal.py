from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.input.thermal.areas_ini import (
    InputThermalAreasIni,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.thermal.cluster.cluster import (
    InputThermalClusters,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.thermal.prepro.prepro import (
    InputThermalPrepro,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.thermal.series.series import (
    InputThermalSeries,
)


class InputThermal(FolderNode):
    def build(self) -> TREE:
        children: TREE = {
            "clusters": InputThermalClusters(
                self.context, self.config.next_file("clusters")
            ),
            "prepro": InputThermalPrepro(
                self.context, self.config.next_file("prepro")
            ),
            "series": InputThermalSeries(
                self.context, self.config.next_file("series")
            ),
            "areas": InputThermalAreasIni(
                self.context, self.config.next_file("areas.ini")
            ),
        }
        return children
