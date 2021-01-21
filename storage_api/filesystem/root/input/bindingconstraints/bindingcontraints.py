from storage_api.filesystem.config.model import Config
from storage_api.filesystem.folder_node import FolderNode
from storage_api.filesystem.inode import TREE
from storage_api.filesystem.root.input.bindingconstraints.bindingconstraints_ini import (
    BindingConstraintsIni,
)
from storage_api.filesystem.root.input.bindingconstraints.item import (
    BindingConstraintsItem,
)


class BindingConstraints(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            bind: BindingConstraintsItem(config.next_file(f"{bind}.txt"))
            for bind in config.bindings
        }

        children["bindingconstraints"] = BindingConstraintsIni(
            config.next_file("bindingconstraints.ini")
        )

        return children
