from antarest.storage.business.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.business.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.storage.business.rawstudy.model.filesystem.inode import TREE
from antarest.storage.business.rawstudy.model.filesystem.root.input.areas.item.optimization import (
    InputAreasOptimization,
)
from antarest.storage.business.rawstudy.model.filesystem.root.input.areas.item.ui import (
    InputAreasUi,
)


class InputAreasItem(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            "ui": InputAreasUi(self.context, config.next_file("ui.ini")),
            "optimization": InputAreasOptimization(
                self.context,
                config.next_file("optimization.ini"),
            ),
        }
        return children
