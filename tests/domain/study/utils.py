from typing import Optional, List

from api_iso_antares.domain.study.inode import TREE, INode
from api_iso_antares.domain.study.default_node import DefaultNode


class TestSubNode(INode[int]):
    def __init__(self, value: int):
        self.value = value

    def get(self, url: Optional[List[str]] = None) -> int:
        return self.value

    def save(self, data: int, url: Optional[List[str]] = None) -> None:
        self.value = data

    def validate(self, data: int) -> None:
        pass


class TestDefaultNode(DefaultNode):
    def __init__(self, children: TREE):
        self.children = children
