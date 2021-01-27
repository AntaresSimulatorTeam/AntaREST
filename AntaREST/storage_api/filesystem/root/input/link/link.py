from AntaREST.storage_api.filesystem.config.model import Config
from AntaREST.storage_api.filesystem.folder_node import FolderNode
from AntaREST.storage_api.filesystem.inode import TREE
from AntaREST.storage_api.filesystem.root.input.link.area.area import (
    InputLinkArea,
)


class InputLink(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            a: InputLinkArea(config.next_file(a), area=a)
            for a in config.area_names()
        }
        return children
