from antarest.storage_api.filesystem.config.model import StudyConfig
from antarest.storage_api.filesystem.folder_node import FolderNode
from antarest.storage_api.filesystem.inode import TREE
from antarest.storage_api.filesystem.root.input.bindingconstraints.bindingconstraints_ini import (
    BindingConstraintsIni,
)
from antarest.storage_api.filesystem.root.input.bindingconstraints.item import (
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
