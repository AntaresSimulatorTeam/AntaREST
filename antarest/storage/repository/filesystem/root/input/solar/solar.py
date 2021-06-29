from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.input.solar.prepro.prepro import (
    InputSolarPrepro,
)
from antarest.storage.repository.filesystem.root.input.solar.series.series import (
    InputSolarSeries,
)


class InputSolar(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            "prepro": InputSolarPrepro(
                self.context, config.next_file("prepro")
            ),
            "series": InputSolarSeries(
                self.context, config.next_file("series")
            ),
        }
        return children
