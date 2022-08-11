from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.input.areas.item.adequacy_patch import (
    InputAreasAdequacyPatch,
)
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
        if self.config.version >= 830:
            children["adequacy_patch"] = InputAreasAdequacyPatch(
                self.context, self.config.next_file("adequacy_patch.ini")
            )
        return children
