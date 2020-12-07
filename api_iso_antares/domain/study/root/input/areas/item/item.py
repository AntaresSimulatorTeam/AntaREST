from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.folder_node import FolderNode
from api_iso_antares.domain.study.inode import TREE
from api_iso_antares.domain.study.root.input.areas.item.optimization import (
    InputAreasOptimization,
)
from api_iso_antares.domain.study.root.input.areas.item.ui import InputAreasUi


class InputAreasItem(FolderNode):
    def __init__(self, config: Config):
        children: TREE = {
            "ui": InputAreasUi(config.next_file("ui.ini")),
            "optimization": InputAreasOptimization(
                config.next_file("optimization.ini")
            ),
        }
        FolderNode.__init__(self, children)
