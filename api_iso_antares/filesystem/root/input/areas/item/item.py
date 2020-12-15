from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.input.areas.item.optimization import (
    InputAreasOptimization,
)
from api_iso_antares.filesystem.root.input.areas.item.ui import InputAreasUi


class InputAreasItem(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            "ui": InputAreasUi(config.next_file("ui.ini")),
            "optimization": InputAreasOptimization(
                config.next_file("optimization.ini")
            ),
        }
        return children
