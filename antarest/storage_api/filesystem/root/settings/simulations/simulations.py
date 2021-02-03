from antarest.storage_api.filesystem.config.model import StudyConfig
from antarest.storage_api.filesystem.folder_node import FolderNode
from antarest.storage_api.filesystem.inode import TREE


class SettingsSimulations(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {}
        return children
