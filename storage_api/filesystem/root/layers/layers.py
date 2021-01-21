from storage_api.filesystem.config.model import Config
from storage_api.filesystem.folder_node import FolderNode
from storage_api.filesystem.inode import TREE
from storage_api.filesystem.root.layers.layer_ini import LayersIni


class Layers(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {"layers": LayersIni(config.next_file("layers.ini"))}
        return children
