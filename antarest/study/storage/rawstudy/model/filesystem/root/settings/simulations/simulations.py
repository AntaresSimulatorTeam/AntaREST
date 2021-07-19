from antarest.storage.business.rawstudy.model.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.business.rawstudy.model.filesystem.folder_node import FolderNode
from antarest.storage.business.rawstudy.model.filesystem.inode import TREE


class SettingsSimulations(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {}
        return children
