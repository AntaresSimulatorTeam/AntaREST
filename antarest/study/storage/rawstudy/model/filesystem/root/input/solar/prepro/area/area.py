from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.input.solar.prepro.area.conversion import (
    InputSolarPreproAreaConversation,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.solar.prepro.area.data import (
    InputSolarPreproAreaData,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.solar.prepro.area.k import (
    InputSolarPreproAreaK,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.solar.prepro.area.settings import (
    InputSolarPreproAreaSettings,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.solar.prepro.area.translation import (
    InputSolarPreproAreaTranslation,
)


class InputSolarPreproArea(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            "conversion": InputSolarPreproAreaConversation(
                self.context, config.next_file("conversion.txt")
            ),
            "data": InputSolarPreproAreaData(
                self.context, config.next_file("data.txt")
            ),
            "k": InputSolarPreproAreaK(
                self.context, config.next_file("k.txt")
            ),
            "translation": InputSolarPreproAreaTranslation(
                self.context, config.next_file("translation.txt")
            ),
            "settings": InputSolarPreproAreaSettings(
                self.context, config.next_file("settings.ini")
            ),
        }
        return children
