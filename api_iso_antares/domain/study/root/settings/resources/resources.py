from typing import Optional

from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.folder_node import FolderNode
from api_iso_antares.domain.study.inode import TREE
from api_iso_antares.domain.study.root.settings.resources.study_icon import (
    StudyIcon,
)


class Resources(FolderNode):
    def __init__(self, config: Config):
        children = {"study": StudyIcon(config.next_file("study.icon"))}
        FolderNode.__init__(self, children)
