from antarest.storage.repository.filesystem.config.model import (
    FileStudyTreeConfig,
)
from antarest.storage.repository.filesystem.folder_node import FolderNode
from antarest.storage.repository.filesystem.inode import TREE
from antarest.storage.repository.filesystem.root.settings.resources.study_ico import (
    StudyIcon,
)


class Resources(FolderNode):
    def build(self, config: FileStudyTreeConfig) -> TREE:
        children: TREE = {
            "study": StudyIcon(self.context, config.next_file("study.ico"))
        }
        return children
