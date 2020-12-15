from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE


class SettingsSimulations(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {}
        return children
