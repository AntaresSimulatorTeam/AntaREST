from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.input.areas.item.optimization import (
    InputAreasOptimization,
)
from antarest.storage.repository.filesystem.root.input.areas.item.ui import (
    InputAreasUi,
)


class InputAreasItem(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            "ui": InputAreasUi(self.context, config.next_file("ui.ini")),
            "optimization": InputAreasOptimization(
                self.context,
                config.next_file("optimization.ini"),
            ),
        }
        return children
