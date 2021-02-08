from antarest.storage.filesystem.config.model import StudyConfig
from antarest.storage.filesystem.folder_node import FolderNode
from antarest.storage.filesystem.inode import TREE
from antarest.storage.filesystem.root.input.link.area.area import (
    InputLinkArea,
)


class InputLink(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            a: InputLinkArea(config.next_file(a), area=a)
            for a in config.area_names()
        }
        return children
