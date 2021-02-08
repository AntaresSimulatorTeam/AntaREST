from antarest.storage.filesystem.config.model import StudyConfig
from antarest.storage.filesystem.folder_node import FolderNode
from antarest.storage.filesystem.inode import TREE
from antarest.storage.filesystem.root.input.wind.prepro.prepro import (
    InputWindPrepro,
)
from antarest.storage.filesystem.root.input.wind.series.series import (
    InputWindSeries,
)


class InputWind(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            "prepro": InputWindPrepro(config.next_file("prepro")),
            "series": InputWindSeries(config.next_file("series")),
        }
        return children
