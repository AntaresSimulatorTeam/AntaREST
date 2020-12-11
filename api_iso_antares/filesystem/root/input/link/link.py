from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.input.link.area.area import (
    InputLinkArea,
)


class InputLink(FolderNode):
    def __init__(self, config: Config):
        children: TREE = {
            a: InputLinkArea(config.next_file(a), area=a)
            for a in config.area_names
        }
        FolderNode.__init__(self, config, children)
