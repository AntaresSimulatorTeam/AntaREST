from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.input.areas.item.optimization import (
    InputAreasOptimization,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.areas.item.ui import (
    InputAreasUi,
)


class InputAreasItem(FolderNode):
    def build(self) -> TREE:
        children: TREE = {
            "ui": InputAreasUi(self.context, self.config.next_file("ui.ini")),
            "optimization": InputAreasOptimization(
                self.context,
                self.config.next_file("optimization.ini"),
            ),
        }
        return children
