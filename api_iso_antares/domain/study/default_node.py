from typing import List, Dict, Optional, Tuple

from api_iso_antares.custom_types import JSON
from api_iso_antares.domain.study.inode import INode, TREE


class DefaultNode(INode[JSON]):
    def __init__(self, children: TREE) -> None:
        self.children: TREE = children

    def get(self, url: Optional[List[str]] = None) -> JSON:
        if url:
            name, sub_url = self.extract_child(url)
            return self.children[name].get(sub_url)
        else:
            json = {name: node.get() for name, node in self.children.items()}
            self.validate(json)
            return json

    def save(self, data: JSON, url: Optional[List[str]] = None) -> None:
        url = url or []
        if url:
            name, sub_url = self.extract_child(url)
            return self.children[name].save(data, sub_url)
        else:
            self.validate(data)
            for key in data:
                self.children[key].save(data[key])

    def validate(self, data: JSON) -> None:
        for key in data:
            assert key in self.children

    def extract_child(self, url: List[str]) -> Tuple[str, List[str]]:
        name, sub_url = url[0], url[1:]
        if name not in self.children:
            raise NameError(
                f"{name} not a children of {self.__class__.__name__}"
            )
        return name, sub_url
