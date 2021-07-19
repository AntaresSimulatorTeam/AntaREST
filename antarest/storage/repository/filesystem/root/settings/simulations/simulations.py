from antarest.storage.repository.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE


class SettingsSimulations(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {}
        return children
