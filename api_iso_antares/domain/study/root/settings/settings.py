from typing import Optional

from api_iso_antares.custom_types import JSON
from api_iso_antares.domain.study.config import Config
from api_iso_antares.domain.study.default_node import DefaultNode
from api_iso_antares.domain.study.inode import TREE
from api_iso_antares.domain.study.root.settings.resources.resources import (
    Resources,
)


class Settings(DefaultNode):
    def __init__(self, config: Config, children: Optional[TREE] = None):
        DefaultNode.__init__(self)
        self.children = children or {
            "resources": Resources(config.next_file("resources"))
        }
