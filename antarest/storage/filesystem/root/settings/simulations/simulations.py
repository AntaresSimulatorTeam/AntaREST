from antarest.storage.filesystem.config.model import StudyConfig
from antarest.storage.filesystem.folder_node import FolderNode
from antarest.storage.filesystem.inode import TREE


class SettingsSimulations(FolderNode):
    def build(self, config: StudyConfig) -> TREE:
        children: TREE = {}
        return children
