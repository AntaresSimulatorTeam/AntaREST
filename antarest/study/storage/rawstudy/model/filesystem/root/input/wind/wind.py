from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.input.wind.prepro.prepro import (
    InputWindPrepro,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.wind.series.series import (
    InputWindSeries,
)


class InputWind(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            "prepro": InputWindPrepro(
                self.context, config.next_file("prepro")
            ),
            "series": InputWindSeries(
                self.context, config.next_file("series")
            ),
        }
        return children
