from antarest.study.storage.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.study.storage.rawstudy.model.filesystem.inode import TREE
from antarest.study.storage.rawstudy.model.filesystem.root.layers.layer_ini import LayersIni


class Layers(FolderNode):
    def build(self) -> TREE:
        children: TREE = {"layers": LayersIni(self.context, self.config.next_file("layers.ini"))}
        return children
