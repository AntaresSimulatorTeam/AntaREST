from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.input.areas.item.item import (
    InputAreasItem,
)
from api_iso_antares.filesystem.root.input.areas.list import InputAreasList
from api_iso_antares.filesystem.root.input.areas.sets import InputAreasSets


class InputAreas(FolderNode):
    def __init__(self, config: Config):
        children: TREE = {
            a: InputAreasItem(config.next_file(a)) for a in config.area_names
        }
        children["list"] = InputAreasList(config.next_file("list.txt"))
        children["sets"] = InputAreasSets(config.next_file("sets.ini"))
        FolderNode.__init__(self, config, children)
