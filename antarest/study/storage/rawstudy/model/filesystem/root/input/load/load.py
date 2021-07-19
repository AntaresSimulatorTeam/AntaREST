from antarest.storage.business.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.business.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.storage.business.rawstudy.model.filesystem.inode import TREE
from antarest.storage.business.rawstudy.model.filesystem.root.input.load.prepro.prepro import (
    InputLoadPrepro,
)
from antarest.storage.business.rawstudy.model.filesystem.root.input.load.series.series import (
    InputLoadSeries,
)


class InputLoad(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            "prepro": InputLoadPrepro(
                self.context, config.next_file("prepro")
            ),
            "series": InputLoadSeries(
                self.context, config.next_file("series")
            ),
        }
        return children
