from antarest.storage.repository.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.layers.layer_ini import (
    LayersIni,
)


class Layers(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            "layers": LayersIni(self.context, config.next_file("layers.ini"))
        }
        return children
