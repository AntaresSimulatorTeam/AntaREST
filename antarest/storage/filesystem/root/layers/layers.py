from antarest.storage.filesystem.config.model import StudyConfig
from antarest.storage.filesystem.folder_node import FolderNode
from antarest.storage.filesystem.inode import TREE
from antarest.storage.filesystem.root.layers.layer_ini import LayersIni


class Layers(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {"layers": LayersIni(config.next_file("layers.ini"))}
        return children
