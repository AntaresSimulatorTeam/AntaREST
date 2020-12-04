from abc import ABC
from typing import List, Dict

from api_iso_antares.custom_types import JSON
from api_iso_antares.domain.study.inode import INode, TREE


class DefaultNode(INode, ABC):
    def __init__(self) -> None:
        self.children: TREE = dict()

    def get(self, url: List[str]) -> JSON:
        if url:
            name, sub_url = url[0], url[1:]
            if name in self.children.keys():
                return self.children[name].get(sub_url)
            else:
                raise NameError(
                    f"{name} not a children of {self.__class__.__name__}"
                )
        else:
            return self.to_json()

    def to_json(self) -> JSON:
        return {name: node.to_json() for name, node in self.children.items()}

    def validate(self, data: JSON):
        pass
