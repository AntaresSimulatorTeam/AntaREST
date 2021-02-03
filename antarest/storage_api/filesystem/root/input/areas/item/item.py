from antarest.storage_api.filesystem.config.model import StudyConfig
from antarest.storage_api.filesystem.folder_node import FolderNode
from antarest.storage_api.filesystem.inode import TREE
from antarest.storage_api.filesystem.root.input.areas.item.optimization import (
    InputAreasOptimization,
)
from antarest.storage_api.filesystem.root.input.areas.item.ui import (
    InputAreasUi,
)


class InputAreasItem(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            "ui": InputAreasUi(config.next_file("ui.ini")),
            "optimization": InputAreasOptimization(
                config.next_file("optimization.ini")
            ),
        }
        return children
