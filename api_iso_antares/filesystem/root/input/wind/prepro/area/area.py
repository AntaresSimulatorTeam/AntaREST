from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.input.wind.prepro.area.conversion import (
    InputWindPreproAreaConversation,
)
from api_iso_antares.filesystem.root.input.wind.prepro.area.data import (
    InputWindPreproAreaData,
)
from api_iso_antares.filesystem.root.input.wind.prepro.area.k import (
    InputWindPreproAreaK,
)
from api_iso_antares.filesystem.root.input.wind.prepro.area.settings import (
    InputWindPreproAreaSettings,
)
from api_iso_antares.filesystem.root.input.wind.prepro.area.translation import (
    InputWindPreproAreaTranslation,
)


class InputWindPreproArea(FolderNode):
    def __init__(self, config: Config):
        children: TREE = {
            "conversion": InputWindPreproAreaConversation(
                config.next_file("conversion.txt")
            ),
            "data": InputWindPreproAreaData(config.next_file("data.txt")),
            "k": InputWindPreproAreaK(config.next_file("k.txt")),
            "translation": InputWindPreproAreaTranslation(
                config.next_file("translation.txt")
            ),
            "settings": InputWindPreproAreaSettings(
                config.next_file("settings.ini")
            ),
        }
        FolderNode.__init__(self, config, children)
