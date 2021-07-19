from antarest.storage.business.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.business.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.storage.business.rawstudy.model.filesystem.inode import TREE
from antarest.storage.business.rawstudy.model.filesystem.root.input.bindingconstraints.bindingconstraints_ini import (
    BindingConstraintsIni,
)
from antarest.storage.business.rawstudy.model.filesystem.root.input.bindingconstraints.item import (
    BindingConstraintsItem,
)


class BindingConstraints(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            bind: BindingConstraintsItem(
                self.context, config.next_file(f"{bind}.txt")
            )
            for bind in config.bindings
        }

        children["bindingconstraints"] = BindingConstraintsIni(
            self.context, config.next_file("bindingconstraints.ini")
        )

        return children
