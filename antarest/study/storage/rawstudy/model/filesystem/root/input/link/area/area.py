from antarest.storage.business.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.business.rawstudy.model.filesystem.context import ContextServer
from antarest.storage.business.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.storage.business.rawstudy.model.filesystem.inode import TREE
from antarest.storage.business.rawstudy.model.filesystem.root.input.link.area.link import (
    InputLinkAreaLink,
)
from antarest.storage.business.rawstudy.model.filesystem.root.input.link.area.properties import (
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
