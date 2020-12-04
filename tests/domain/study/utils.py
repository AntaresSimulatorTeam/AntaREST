from api_iso_antares.custom_types import JSON
from api_iso_antares.domain.study.inode import TREE
from api_iso_antares.domain.study.default_node import DefaultNode


class TestSubNode(DefaultNode):
    def __init__(self, return_value):
        self.return_value = return_value

    def to_json(self) -> JSON:
        return self.return_value


class TestDefaultNode(DefaultNode):
    def __init__(self, children: TREE):
        self.children = children
