from antarest.storage.business.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.business.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.storage.business.rawstudy.model.filesystem.inode import TREE
from antarest.storage.business.rawstudy.model.filesystem.root.input.link.area.area import (
    InputLinkArea,
)


class InputLink(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            a: InputLinkArea(self.context, config.next_file(a), area=a)
            for a in config.area_names()
        }
        return children
