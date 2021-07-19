from antarest.storage.repository.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.repository.filesystem.context import ContextServer
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.input.link.area.link import (
    InputLinkAreaLink,
)
from antarest.storage.repository.filesystem.root.input.link.area.properties import (
    InputLinkAreaProperties,
)


class InputLinkArea(FolderNode):
    def __init__(
        self, context: ContextServer, config: FileStudyTreeConfig, area: str
    ):
        FolderNode.__init__(self, context, config)
        self.area = area

    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            l: InputLinkAreaLink(self.context, config.next_file(f"{l}.txt"))
            for l in config.get_links(self.area)
        }
        children["properties"] = InputLinkAreaProperties(
            self.context, config.next_file("properties.ini"), area=self.area
        )

        return children
