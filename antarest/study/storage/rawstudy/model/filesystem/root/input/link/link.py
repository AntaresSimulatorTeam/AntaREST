from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.input.link.area.area import (
    InputLinkArea,
)


class InputLink(FolderNode):
    def build(self) -> TREE:
        children: TREE = {
            a: InputLinkArea(self.context, self.config.next_file(a), area=a)
            for a in self.config.area_names()
        }
        return children
