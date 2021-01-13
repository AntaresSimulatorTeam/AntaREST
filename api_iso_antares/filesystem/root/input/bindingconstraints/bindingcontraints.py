from api_iso_antares.filesystem.config.model import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.input.bindingconstraints.bindingconstraints_ini import (
    BindingConstraintsIni,
)
from api_iso_antares.filesystem.root.input.bindingconstraints.item import (
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
