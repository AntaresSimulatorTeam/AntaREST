from AntaREST.storage_api.filesystem.config.model import Config
from AntaREST.storage_api.filesystem.folder_node import FolderNode
from AntaREST.storage_api.filesystem.inode import TREE
from AntaREST.storage_api.filesystem.root.input.link.area.link import (
    InputLinkAreaLink,
)
from AntaREST.storage_api.filesystem.root.input.link.area.properties import (
    InputLinkAreaProperties,
)


class InputLinkArea(FolderNode):
    def __init__(self, config: Config, area: str):
        FolderNode.__init__(self, config)
        self.area = area

    def build(self, config: Config) -> TREE:
        children: TREE = {
            l: InputLinkAreaLink(config.next_file(f"{l}.txt"))
            for l in config.get_links(self.area)
        }
        children["properties"] = InputLinkAreaProperties(
            config.next_file("properties.ini"), area=self.area
        )

        return children
