from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.input.thermal.areas_ini import (
    InputThermalAreasIni,
)
from antarest.storage.repository.filesystem.root.input.thermal.cluster.cluster import (
    InputThermalClusters,
)
from antarest.storage.repository.filesystem.root.input.thermal.prepro.prepro import (
    InputThermalPrepro,
)
from antarest.storage.repository.filesystem.root.input.thermal.series.series import (
    InputThermalSeries,
)


class InputThermal(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
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
