from antarest.storage.business.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.business.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.storage.business.rawstudy.model.filesystem.inode import TREE
from antarest.storage.business.rawstudy.model.filesystem.root.input.load.prepro.area.area import (
    InputLoadPreproArea,
)
from antarest.storage.business.rawstudy.model.filesystem.root.input.load.prepro.correlation import (
    InputLoadPreproCorrelation,
)


class InputLoadPrepro(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            a: InputLoadPreproArea(self.context, config.next_file(a))
            for a in config.area_names()
        }
        children["correlation"] = InputLoadPreproCorrelation(
            self.context, config.next_file("correlation.ini")
        )
        return children
