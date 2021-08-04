from antarest.study.storage.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.matrix.input_series_matrix import (
    InputSeriesMatrix,
)
from antarest.study.storage.rawstudy.model.filesystem.root.input.bindingconstraints.bindingconstraints_ini import (
    BindingConstraintsIni,
)


class BindingConstraints(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            bind: InputSeriesMatrix(
                self.context, config.next_file(f"{bind}.txt")
            )
            for bind in config.bindings
        }

        children["bindingconstraints"] = BindingConstraintsIni(
            self.context, config.next_file("bindingconstraints.ini")
        )

        return children
