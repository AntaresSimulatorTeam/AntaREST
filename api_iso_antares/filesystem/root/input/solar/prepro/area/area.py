from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.input.solar.prepro.area.conversion import (
    InputSolarPreproAreaConversation,
)
from api_iso_antares.filesystem.root.input.solar.prepro.area.data import (
    InputSolarPreproAreaData,
)
from api_iso_antares.filesystem.root.input.solar.prepro.area.k import (
    InputSolarPreproAreaK,
)
from api_iso_antares.filesystem.root.input.solar.prepro.area.settings import (
    InputSolarPreproAreaSettings,
)
from api_iso_antares.filesystem.root.input.solar.prepro.area.translation import (
    InputSolarPreproAreaTranslation,
)


class InputSolarPreproArea(FolderNode):
    def __init__(self, config: Config):
        children: TREE = {
            "conversation": InputSolarPreproAreaConversation(
                config.next_file("conversation.txt")
            ),
            "data": InputSolarPreproAreaData(config.next_file("data.txt")),
            "k": InputSolarPreproAreaK(config.next_file("k.txt")),
            "translation": InputSolarPreproAreaTranslation(
                config.next_file("translation.txt")
            ),
            "settings": InputSolarPreproAreaSettings(
                config.next_file("settings.ini")
            ),
        }
        FolderNode.__init__(self, children)
