from antarest.study.storage.rawstudy.model.filesystem.common.prepro import (
    PreproCorrelation,
)
from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.input.hydro.prepro.area.area import (
    InputHydroPreproArea,
)


class InputHydroPrepro(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            a: InputHydroPreproArea(self.context, config.next_file(a))
            for a in config.area_names()
        }
        children["correlation"] = PreproCorrelation(
            self.context, config.next_file("correlation.ini")
        )
        return children
