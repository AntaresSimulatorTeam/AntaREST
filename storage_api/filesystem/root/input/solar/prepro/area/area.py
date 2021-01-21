from storage_api.filesystem.config.model import Config
from storage_api.filesystem.folder_node import FolderNode
from storage_api.filesystem.inode import TREE
from storage_api.filesystem.root.input.solar.prepro.area.conversion import (
    InputSolarPreproAreaConversation,
)
from storage_api.filesystem.root.input.solar.prepro.area.data import (
    InputSolarPreproAreaData,
)
from storage_api.filesystem.root.input.solar.prepro.area.k import (
    InputSolarPreproAreaK,
)
from storage_api.filesystem.root.input.solar.prepro.area.settings import (
    InputSolarPreproAreaSettings,
)
from storage_api.filesystem.root.input.solar.prepro.area.translation import (
    InputSolarPreproAreaTranslation,
)


class InputSolarPreproArea(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            "conversion": InputSolarPreproAreaConversation(
                config.next_file("conversion.txt")
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
        return children
