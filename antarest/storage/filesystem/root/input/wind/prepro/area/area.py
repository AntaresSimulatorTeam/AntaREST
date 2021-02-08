from antarest.storage.filesystem.config.model import StudyConfig
from antarest.storage.filesystem.folder_node import FolderNode
from antarest.storage.filesystem.inode import TREE
from antarest.storage.filesystem.root.input.wind.prepro.area.conversion import (
    InputWindPreproAreaConversation,
)
from antarest.storage.filesystem.root.input.wind.prepro.area.data import (
    InputWindPreproAreaData,
)
from antarest.storage.filesystem.root.input.wind.prepro.area.k import (
    InputWindPreproAreaK,
)
from antarest.storage.filesystem.root.input.wind.prepro.area.settings import (
    InputWindPreproAreaSettings,
)
from antarest.storage.filesystem.root.input.wind.prepro.area.translation import (
    InputWindPreproAreaTranslation,
)


class InputWindPreproArea(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
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
