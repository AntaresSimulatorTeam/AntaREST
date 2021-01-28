from antarest.storage_api.filesystem.config.model import Config
from antarest.storage_api.filesystem.folder_node import FolderNode
from antarest.storage_api.filesystem.inode import TREE


class SettingsSimulations(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {}
        return children
