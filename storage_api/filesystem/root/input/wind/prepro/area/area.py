from storage_api.filesystem.config.model import Config
from storage_api.filesystem.folder_node import FolderNode
from storage_api.filesystem.inode import TREE
from storage_api.filesystem.root.input.wind.prepro.area.conversion import (
    InputWindPreproAreaConversation,
)
from storage_api.filesystem.root.input.wind.prepro.area.data import (
    InputWindPreproAreaData,
)
from storage_api.filesystem.root.input.wind.prepro.area.k import (
    InputWindPreproAreaK,
)
from storage_api.filesystem.root.input.wind.prepro.area.settings import (
    InputWindPreproAreaSettings,
)
from storage_api.filesystem.root.input.wind.prepro.area.translation import (
    InputWindPreproAreaTranslation,
)


class InputWindPreproArea(FolderNode):
    def build(self, config: Config) -> TREE:
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
        return children
