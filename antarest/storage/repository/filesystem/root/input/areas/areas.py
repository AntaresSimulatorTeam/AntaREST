from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.input.areas.item.item import (
    InputAreasItem,
)
from antarest.storage.repository.filesystem.root.input.areas.list import (
    InputAreasList,
)
from antarest.storage.repository.filesystem.root.input.areas.sets import (
    InputAreasSets,
)


class InputAreas(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            a: InputAreasItem(self.context, config.next_file(a))
            for a in config.area_names()
        }
        children["list"] = InputAreasList(
            self.context, config.next_file("list.txt")
        )
        children["sets"] = InputAreasSets(
            self.context, config.next_file("sets.ini")
        )
        return children
