from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.folder_node import FolderNode
from api_iso_antares.domain.study.inode import TREE
from api_iso_antares.domain.study.root.layers.layer_ini import LayersIni


class Layers(FolderNode):
    def __init__(self, config: Config):
        children: TREE = {"layers": LayersIni(config.next_file("layers.ini"))}
        FolderNode.__init__(self, children)
