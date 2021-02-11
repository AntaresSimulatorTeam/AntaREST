from antarest.storage.repository.filesystem.config.model import StudyConfig
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.input.bindingconstraints.bindingconstraints_ini import (
    BindingConstraintsIni,
)
from antarest.storage.repository.filesystem.root.input.bindingconstraints.item import (
    BindingConstraintsItem,
)


class BindingConstraints(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {
            bind: BindingConstraintsItem(config.next_file(f"{bind}.txt"))
            for bind in config.bindings
        }

        children["bindingconstraints"] = BindingConstraintsIni(
            config.next_file("bindingconstraints.ini")
        )

        return children
