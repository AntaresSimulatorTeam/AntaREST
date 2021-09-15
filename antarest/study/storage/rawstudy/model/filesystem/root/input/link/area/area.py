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
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import (
    InputSeriesMatrix,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.link.area.properties import (
    InputLinkAreaProperties,
)


class InputLinkArea(FolderNode):
    def __init__(
        self, context: ContextServer, config: FileStudyTreeConfig, area: str
    ):
        FolderNode.__init__(self, context, config)
        self.area = area

    def build(self) -> TREE:
        children: TREE = {
            l: InputSeriesMatrix(
                self.context, self.config.next_file(f"{l}.txt")
            )
            for l in self.config.get_links(self.area)
        }
        children["properties"] = InputLinkAreaProperties(
            self.context,
            self.config.next_file("properties.ini"),
            area=self.area,
        )

        return children
