from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.input.load.prepro.area.conversion import (
    InputLoadPreproAreaConversation,
)
from api_iso_antares.filesystem.root.input.load.prepro.area.data import (
    InputLoadPreproAreaData,
)
from api_iso_antares.filesystem.root.input.load.prepro.area.k import (
    InputLoadPreproAreaK,
)
from api_iso_antares.filesystem.root.input.load.prepro.area.settings import (
    InputLoadPreproAreaSettings,
)
from api_iso_antares.filesystem.root.input.load.prepro.area.translation import (
    InputLoadPreproAreaTranslation,
)


class InputLoadPreproArea(FolderNode):
    def __init__(self, config: Config):
        children: TREE = {
            "conversion": InputLoadPreproAreaConversation(
                config.next_file("conversion.txt")
            ),
            "data": InputLoadPreproAreaData(config.next_file("data.txt")),
            "k": InputLoadPreproAreaK(config.next_file("k.txt")),
            "translation": InputLoadPreproAreaTranslation(
                config.next_file("translation.txt")
            ),
            "settings": InputLoadPreproAreaSettings(
                config.next_file("settings.ini")
            ),
        }
        FolderNode.__init__(self, config, children)
