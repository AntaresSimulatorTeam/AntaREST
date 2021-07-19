from antarest.storage.business.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.business.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.storage.business.rawstudy.model.filesystem.inode import TREE
from antarest.storage.business.rawstudy.model.filesystem.root.input.thermal.areas_ini import (
    InputThermalAreasIni,
)
from antarest.storage.business.rawstudy.model.filesystem.root.input.thermal.cluster.cluster import (
    InputThermalClusters,
)
from antarest.storage.business.rawstudy.model.filesystem.root.input.thermal.prepro.prepro import (
    InputThermalPrepro,
)
from antarest.storage.business.rawstudy.model.filesystem.root.input.thermal.series.series import (
    InputThermalSeries,
)


class InputThermal(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            "clusters": InputThermalClusters(
                self.context, config.next_file("clusters")
            ),
            "prepro": InputThermalPrepro(
                self.context, config.next_file("prepro")
            ),
            "series": InputThermalSeries(
                self.context, config.next_file("series")
            ),
            "areas": InputThermalAreasIni(
                self.context, config.next_file("areas.ini")
            ),
        }
        return children
