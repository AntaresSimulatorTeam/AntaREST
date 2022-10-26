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
    def build(self) -> TREE:
        children: TREE = {
            binding.id: InputSeriesMatrix(
                self.context, self.config.next_file(f"{binding.id}.txt")
            )
            # todo get the freq of binding to set the default empty matrix
            for binding in self.config.bindings
        }

        children["bindingconstraints"] = BindingConstraintsIni(
            self.context, self.config.next_file("bindingconstraints.ini")
        )

        return children
