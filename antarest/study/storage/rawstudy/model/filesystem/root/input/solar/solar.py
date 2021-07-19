from antarest.storage.business.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.business.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.storage.business.rawstudy.model.filesystem.inode import TREE
from antarest.storage.business.rawstudy.model.filesystem.root.input.solar.prepro.prepro import (
    InputSolarPrepro,
)
from antarest.storage.business.rawstudy.model.filesystem.root.input.solar.series.series import (
    InputSolarSeries,
)


class InputSolar(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            "prepro": InputSolarPrepro(
                self.context, config.next_file("prepro")
            ),
            "series": InputSolarSeries(
                self.context, config.next_file("series")
            ),
        }
        return children
