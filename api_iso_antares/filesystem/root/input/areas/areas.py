from api_iso_antares.filesystem.config.model import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.input.areas.item.item import (
    InputAreasItem,
)
from api_iso_antares.filesystem.root.input.areas.list import InputAreasList
from api_iso_antares.filesystem.root.input.areas.sets import InputAreasSets


class InputAreas(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            a: InputAreasItem(config.next_file(a)) for a in config.area_names()
        }
        children["list"] = InputAreasList(config.next_file("list.txt"))
        children["sets"] = InputAreasSets(config.next_file("sets.ini"))
        return children
