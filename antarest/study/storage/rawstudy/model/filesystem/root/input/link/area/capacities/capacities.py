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


class InputLinkAreaCapacities(FolderNode):
    def __init__(
        self,
        context: ContextServer,
        config: FileStudyTreeConfig,
        area: str,
    ):
        FolderNode.__init__(self, context, config)
        self.area = area

    def build(self) -> TREE:
        children: TREE = {}
        for area_to in self.config.get_links(self.area):
            children[f"{area_to}_direct"] = InputSeriesMatrix(
                self.context,
                self.config.next_file(f"{area_to}_direct.txt"),
            )
            children[f"{area_to}_indirect"] = InputSeriesMatrix(
                self.context,
                self.config.next_file(f"{area_to}_indirect.txt"),
            )

        return children
