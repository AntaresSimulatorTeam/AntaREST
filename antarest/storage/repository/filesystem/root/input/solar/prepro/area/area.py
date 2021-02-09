from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.input.solar.prepro.area.conversion import (
    InputSolarPreproAreaConversation,
)
from antarest.storage.repository.filesystem.root.input.solar.prepro.area.data import (
    InputSolarPreproAreaData,
)
from antarest.storage.repository.filesystem.root.input.solar.prepro.area.k import (
    InputSolarPreproAreaK,
)
from antarest.storage.repository.filesystem.root.input.solar.prepro.area.settings import (
    InputSolarPreproAreaSettings,
)
from antarest.storage.repository.filesystem.root.input.solar.prepro.area.translation import (
    InputSolarPreproAreaTranslation,
)


class InputSolarPreproArea(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
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
