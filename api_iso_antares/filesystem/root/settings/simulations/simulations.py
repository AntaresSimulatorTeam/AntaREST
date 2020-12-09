from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE


class SettingsSimulations(FolderNode):
    def __init__(self, config: Config):
        children: TREE = {}
        FolderNode.__init__(self, children)
