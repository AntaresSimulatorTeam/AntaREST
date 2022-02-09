from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.user.expansion.candidates import (
    ExpansionCandidates,
)
from antarest.study.storage.rawstudy.model.filesystem.root.user.expansion.capa import (
    ExpansionCapa,
)
from antarest.study.storage.rawstudy.model.filesystem.root.user.expansion.settings import (
    ExpansionSettings,
)


class Expansion(FolderNode):
    def build(self) -> TREE:
        children: TREE = {
            "candidates": ExpansionCandidates(
                self.context, self.config.next_file("candidates.ini")
            ),
            "settings": ExpansionSettings(
                self.context, self.config.next_file("settings.ini")
            ),
            "capa": ExpansionCapa(self.context, self.config.next_file("capa")),
        }
        return children
