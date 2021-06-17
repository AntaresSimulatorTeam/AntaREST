from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.input.wind.prepro.prepro import (
    InputWindPrepro,
)
from antarest.storage.repository.filesystem.root.input.wind.series.series import (
    InputWindSeries,
)


class InputWind(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            "prepro": InputWindPrepro(
                self.context, config.next_file("prepro")
            ),
            "series": InputWindSeries(
                self.context, config.next_file("series")
            ),
        }
        return children
