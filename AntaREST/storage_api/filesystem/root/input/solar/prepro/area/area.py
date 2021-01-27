from AntaREST.storage_api.filesystem.config.model import Config
from AntaREST.storage_api.filesystem.folder_node import FolderNode
from AntaREST.storage_api.filesystem.inode import TREE
from AntaREST.storage_api.filesystem.root.input.solar.prepro.area.conversion import (
    InputSolarPreproAreaConversation,
)
from AntaREST.storage_api.filesystem.root.input.solar.prepro.area.data import (
    InputSolarPreproAreaData,
)
from AntaREST.storage_api.filesystem.root.input.solar.prepro.area.k import (
    InputSolarPreproAreaK,
)
from AntaREST.storage_api.filesystem.root.input.solar.prepro.area.settings import (
    InputSolarPreproAreaSettings,
)
from AntaREST.storage_api.filesystem.root.input.solar.prepro.area.translation import (
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
