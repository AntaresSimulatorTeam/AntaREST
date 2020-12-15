from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.layers.layer_ini import LayersIni


class Layers(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {"layers": LayersIni(config.next_file("layers.ini"))}
        return children
