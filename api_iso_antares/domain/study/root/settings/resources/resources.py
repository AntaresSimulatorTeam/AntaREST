from typing import Optional

from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.default_node import DefaultNode
from api_iso_antares.domain.study.inode import TREE
from api_iso_antares.domain.study.root.settings.resources.study_icon import (
    StudyIcon,
)


class Resources(DefaultNode):
    def __init__(self, config: Config, children: Optional[TREE] = None):
        DefaultNode.__init__(self)
        self.children = children or {
            "study": StudyIcon(config.next_file("study.icon"))
        }
