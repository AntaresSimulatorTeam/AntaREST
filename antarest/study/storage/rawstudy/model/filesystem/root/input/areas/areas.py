from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.context import (
    ContextServer,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.input.areas.item.item import (
    InputAreasItem,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.areas.list import (
    InputAreasList,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.areas.sets import (
    InputAreasSets,
)


class InputAreas(FolderNode):
    def __init__(self, context: ContextServer, config: FileStudyTreeConfig):
        super().__init__(context, config, ["list", "sets"])

    def build(self) -> TREE:
        children: TREE = {
            a: InputAreasItem(self.context, self.config.next_file(a))
            for a in self.config.area_names()
        }
        children["list"] = InputAreasList(
            self.context, self.config.next_file("list.txt")
        )
        children["sets"] = InputAreasSets(
            self.context, self.config.next_file("sets.ini")
        )
        return children
