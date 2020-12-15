from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.input.bindingconstraints.bindingconstraints_ini import (
    BindingConstraintsIni,
)


class BindingConstraints(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {
            "bindingconstraints": BindingConstraintsIni(
                config.next_file("bindingconstraints.ini")
            )
        }
        return children
