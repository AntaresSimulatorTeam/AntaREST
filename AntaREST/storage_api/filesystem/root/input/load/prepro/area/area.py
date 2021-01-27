from AntaREST.storage_api.filesystem.config.model import Config
from AntaREST.storage_api.filesystem.folder_node import FolderNode
from AntaREST.storage_api.filesystem.inode import TREE
from AntaREST.storage_api.filesystem.root.input.load.prepro.area.conversion import (
    InputLoadPreproAreaConversation,
)
from AntaREST.storage_api.filesystem.root.input.load.prepro.area.data import (
    InputLoadPreproAreaData,
)
from AntaREST.storage_api.filesystem.root.input.load.prepro.area.k import (
    InputLoadPreproAreaK,
)
from AntaREST.storage_api.filesystem.root.input.load.prepro.area.settings import (
    InputLoadPreproAreaSettings,
)
from AntaREST.storage_api.filesystem.root.input.load.prepro.area.translation import (
    InputLoadPreproAreaTranslation,
)


class InputLoadPreproArea(FolderNode):
    def build(self, config: Config) -> TREE:
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
        return children
