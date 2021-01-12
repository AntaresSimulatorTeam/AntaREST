from typing import Optional

from api_iso_antares.filesystem.config.model import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.settings.resources.study_ico import (
    StudyIcon,
)


class Resources(FolderNode):
    def build(self, config: Config) -> TREE:
        children: TREE = {"study": StudyIcon(config.next_file("study.ico"))}
        return children
