from antarest.storage.filesystem.config.model import StudyConfig
from antarest.storage.filesystem.folder_node import FolderNode
from antarest.storage.filesystem.inode import TREE
from antarest.storage.filesystem.root.input.solar.prepro.prepro import (
    InputSolarPrepro,
)
from antarest.storage.filesystem.root.input.solar.series.series import (
    InputSolarSeries,
)


class InputSolar(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            "prepro": InputSolarPrepro(config.next_file("prepro")),
            "series": InputSolarSeries(config.next_file("series")),
        }
        return children
