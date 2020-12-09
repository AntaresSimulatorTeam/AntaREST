from typing import Optional

from api_iso_antares.filesystem.config import Config
from api_iso_antares.filesystem.folder_node import FolderNode
from api_iso_antares.filesystem.inode import TREE
from api_iso_antares.filesystem.root.settings.resources.study_icon import (
    StudyIcon,
)


class Resources(FolderNode):
    def __init__(self, config: Config):
        children: TREE = {"study": StudyIcon(config.next_file("study.icon"))}
        FolderNode.__init__(self, children)
