from antarest.storage_api.filesystem.config.model import StudyConfig
from antarest.storage_api.filesystem.folder_node import FolderNode
from antarest.storage_api.filesystem.inode import TREE
from antarest.storage_api.filesystem.root.input.wind.prepro.prepro import (
    InputWindPrepro,
)
from antarest.storage_api.filesystem.root.input.wind.series.series import (
    InputWindSeries,
)


class InputWind(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            "prepro": InputWindPrepro(config.next_file("prepro")),
            "series": InputWindSeries(config.next_file("series")),
        }
        return children
